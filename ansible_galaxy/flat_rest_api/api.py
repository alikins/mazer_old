########################################################################
#
# (C) 2013, James Cammarata <jcammarata@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import json
import six
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import quote as urlquote, urlencode

from ansible_galaxy.flat_rest_api.token import GalaxyToken
from ansible_galaxy.config import runtime
from ansible_galaxy import exceptions
from ansible_galaxy.utils.text import to_native, to_text

# FIXME: would be nice to just use requests, or better, some async https client
from ansible_galaxy.flat_rest_api.urls import open_url

log = logging.getLogger(__name__)


def g_connect(method):
    ''' wrapper to lazily initialize connection info to galaxy '''
    def wrapped(self, *args, **kwargs):
        if not self.initialized:
            log.debug("Initial connection to galaxy_server: %s", self._api_server)
            server_version = self._get_server_api_version()
            if server_version not in self.SUPPORTED_VERSIONS:
                raise exceptions.GalaxyClientError("Unsupported Galaxy server API version: %s" % server_version)

            self.baseurl = '%s/api/%s' % (self._api_server, server_version)
            self.version = server_version  # for future use
            log.debug("Base API: %s", self.baseurl)
            self.initialized = True
        return method(self, *args, **kwargs)
    return wrapped


class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    SUPPORTED_VERSIONS = ['v1']

    def __init__(self, galaxy):
        self.galaxy = galaxy
        self.token = GalaxyToken()
        self._api_server = runtime.GALAXY_SERVER
        self._validate_certs = not galaxy.options.ignore_certs
        self.baseurl = None
        self.version = None
        self.initialized = False
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        self.log.debug('Validate TLS certificates: %s', self._validate_certs)

        # set the API server
        if galaxy.options.api_server != runtime.GALAXY_SERVER:
            self._api_server = galaxy.options.api_server

    def __auth_header(self):
        token = self.token.get()
        if token is None:
            raise exceptions.GalaxyClientError("No access token. You must first use login to authenticate and obtain an access token.")
        return {'Authorization': 'Token ' + token}

    @g_connect
    def __call_galaxy(self, url, args=None, headers=None, method=None):
        if args and not headers:
            headers = self.__auth_header()
        try:
            # self.log.info('%s %s', method, url)
            # self.log.debug('%s %s args=%s', method, url, args)
            # self.log.debug('%s %s headers=%s', method, url, headers)
            resp = open_url(url, data=args, validate_certs=self._validate_certs, headers=headers, method=method,
                            timeout=20)
            self.log.debug('%s %s http_status=%s', method, url, resp.getcode())
            final_url = resp.geturl()
            if final_url != url:
                self.log.debug('%s %s Redirected to: %s', method, url, resp.geturl())
            # self.log.debug('%s %s info:\n%s', method, url, resp.info())
            data = json.loads(to_text(resp.read(), errors='surrogate_or_strict'))
            # self.log.debug('%s %s data: \n%s', method, url, json.dumps(data, indent=2))
        except HTTPError as e:
            self.log.debug('Exception on %s %s', method, url)
            self.log.exception(e)
            res = json.loads(to_text(e.fp.read(), errors='surrogate_or_strict'))
            raise exceptions.GalaxyClientError(res['detail'])
        return data

    @property
    def api_server(self):
        return self._api_server

    @property
    def validate_certs(self):
        return self._validate_certs

    def _get_server_api_version(self):
        """
        Fetches the Galaxy API current version to ensure
        the API server is up and reachable.
        """
        url = '%s/api/' % self._api_server
        try:
            return_data = open_url(url, validate_certs=self._validate_certs)
        except Exception as e:
            raise exceptions.GalaxyClientError("Failed to get data from the API server (%s): %s " % (url, to_native(e)))

        try:
            data = json.loads(to_text(return_data.read(), errors='surrogate_or_strict'))
        except Exception as e:
            raise exceptions.GalaxyClientError("Could not process data from the API server (%s): %s " % (url, to_native(e)))

        if 'current_version' not in data:
            raise exceptions.GalaxyClientError("missing required 'current_version' from server response (%s)" % url)

        return data['current_version']

    @g_connect
    def authenticate(self, github_token):
        """
        Retrieve an authentication token
        """
        url = '%s/tokens/' % self.baseurl
        args = urlencode({"github_token": github_token})
        resp = open_url(url, data=args, validate_certs=self._validate_certs, method="POST")
        data = json.loads(to_text(resp.read(), errors='surrogate_or_strict'))
        return data

    @g_connect
    def create_import_task(self, github_user, github_repo, reference=None, role_name=None):
        """
        Post an import request
        """
        url = '%s/imports/' % self.baseurl
        args = {
            "github_user": github_user,
            "github_repo": github_repo,
            "github_reference": reference if reference else ""
        }
        if role_name:
            args['alternate_role_name'] = role_name
        elif github_repo.startswith('ansible-role'):
            args['alternate_role_name'] = github_repo[len('ansible-role') + 1:]
        data = self.__call_galaxy(url, args=urlencode(args), method='POST')
        if data.get('results', None):
            return data['results']
        return data

    @g_connect
    def get_import_task(self, task_id=None, github_user=None, github_repo=None):
        """
        Check the status of an import task.
        """
        url = '%s/imports/' % self.baseurl
        if task_id is not None:
            url = "%s?id=%d" % (url, task_id)
        elif github_user is not None and github_repo is not None:
            url = "%s?github_user=%s&github_repo=%s" % (url, github_user, github_repo)
        else:
            raise exceptions.GalaxyClientError("Expected task_id or github_user and github_repo")

        data = self.__call_galaxy(url)
        return data['results']

    @g_connect
    def lookup_content_repo_by_name(self, namespace, name):
        namespace = urlquote(namespace)
        name = urlquote(name)

        url = '%s/content/?repository__name=%s&namespace__name=%s' % (self.baseurl, name, namespace)
        data = self.__call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    @g_connect
    def lookup_content_by_name(self, user_name, repo_name, content_name, content_type=None, notify=True):
        content_name = urlquote(content_name)
        repo_name = urlquote(repo_name)

        if notify:
            self.log.info("- downloading content '%s', type '%s',repo_name '%s'  owned by %s", content_name, content_type, repo_name, user_name)

        url = '%s/content/?owner__username=%s&name=%s' % (self.baseurl, user_name, content_name)
        data = self.__call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    @g_connect
    def lookup_role_by_name(self, role_name, notify=True):
        """
        Find a role by name.
        """
        role_name = urlquote(role_name)

        try:
            parts = role_name.split(".")
            user_name = ".".join(parts[0:-1])
            role_name = parts[-1]
            if notify:
                self.log.info("- downloading role '%s', owned by %s", role_name, user_name)
        except Exception as e:
            self.log.exception(e)
            raise exceptions.GalaxyClientError("Invalid role name (%s). Specify role as format: username.rolename" % role_name)

        url = '%s/roles/?owner__username=%s&name=%s' % (self.baseurl, user_name, role_name)
        data = self.__call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    #@g_connect
    #def fetch_content_related(self, related_url):
    #    "Fetch a related item for the given content"
    #    self.log.debug('related_url=%s', related_url)
    #    url = '%s%s' % (self._api_server, related_url)
    #    data = self.__call_galaxy(url)
    #    if len(data["results"]) != 0:
    #        return data["results"][0]
    #    return None

    @g_connect
    def fetch_content_related(self, related_url):
        """
        Fetch the list of related items for the given role.
        The url comes from the 'related' field of the role.
        """
        self.log.debug('related_url=%s', related_url)
        try:
            url = '%s%s?page_size=50' % (self._api_server, related_url)
            data = self.__call_galaxy(url)
            results = data.get('results', None)
            if results is None:
                # not a results list, just return the item
                return data

            done = (data.get('next_link', None) is None)
            while not done:
                url = '%s%s' % (self._api_server, data['next_link'])
                data = self.__call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
            return results
        except Exception as e:
            self.log.exception(e)
            return None

    @g_connect
    def get_list(self, what):
        """
        Fetch the list of items specified.
        """
        try:
            url = '%s/%s/?page_size' % (self.baseurl, what)
            data = self.__call_galaxy(url)
            if "results" in data:
                results = data['results']
            else:
                results = data
            done = True
            if "next" in data:
                done = (data.get('next_link', None) is None)
            while not done:
                url = '%s%s' % (self._api_server, data['next_link'])
                data = self.__call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
            return results
        except Exception as error:
            self.log.exception(error)
            raise exceptions.GalaxyClientError("Failed to download the %s list: %s" % (what, str(error)))

    @g_connect
    def search_roles(self, search, **kwargs):

        search_url = self.baseurl + '/search/roles/?'

        if search:
            search_url += '&autocomplete=' + urlquote(search)

        tags = kwargs.get('tags', None)
        platforms = kwargs.get('platforms', None)
        page_size = kwargs.get('page_size', None)
        author = kwargs.get('author', None)

        if tags and isinstance(tags, six.string_types):
            tags = tags.split(',')
            search_url += '&tags_autocomplete=' + '+'.join(tags)

        if platforms and isinstance(platforms, six.string_types):
            platforms = platforms.split(',')
            search_url += '&platforms_autocomplete=' + '+'.join(platforms)

        if page_size:
            search_url += '&page_size=%s' % page_size

        if author:
            search_url += '&username_autocomplete=%s' % author

        data = self.__call_galaxy(search_url)
        return data

    @g_connect
    def add_secret(self, source, github_user, github_repo, secret):
        url = "%s/notification_secrets/" % self.baseurl
        args = urlencode({
            "source": source,
            "github_user": github_user,
            "github_repo": github_repo,
            "secret": secret
        })
        data = self.__call_galaxy(url, args=args)
        return data

    @g_connect
    def list_secrets(self):
        url = "%s/notification_secrets" % self.baseurl
        data = self.__call_galaxy(url, headers=self.__auth_header())
        return data

    @g_connect
    def remove_secret(self, secret_id):
        url = "%s/notification_secrets/%s/" % (self.baseurl, secret_id)
        data = self.__call_galaxy(url, headers=self.__auth_header(), method='DELETE')
        return data

    @g_connect
    def delete_role(self, github_user, github_repo):
        url = "%s/removerole/?github_user=%s&github_repo=%s" % (self.baseurl, github_user, github_repo)
        data = self.__call_galaxy(url, headers=self.__auth_header(), method='DELETE')
        return data
