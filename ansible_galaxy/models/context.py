########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
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
''' This manages remote shared Ansible objects, mainly roles'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import os

log = logging.getLogger(__name__)


class GalaxyContext(object):
    ''' Keeps global galaxy info '''

    def __init__(self, content_path=None, server=None):

        log.debug('content_path: %s', content_path)
        log.debug('server: %s', server)

        # TODO: server info object
        self.server = server or {'url': None}
        self.content_path = content_path

        # default_content_paths = [os.path.expanduser(p) for p in defaults.DEFAULT_CONTENT_PATH]
        # content_paths = getattr(self.options, 'content_path', [])

    # FIXME: rm
    @property
    def server_url(self):
        if not self.server:
            return None
        return self.server['url']

    @classmethod
    def from_config_and_options(cls, config, options):
        '''Create a GalaxyContext based on config data and cli options'''
        servers_from_config = config.servers
        content_roots_from_config = config.content_roots

        _servers = []
        _option_content_paths = []
        _option_role_paths = []

        # FIXME(alikins): changed my mind, should move this back to cli/ code
        if options:
            if getattr(options, 'content_path', None):
                _option_content_paths = []

                for content_path in options.content_path:
                    _option_content_paths.append(content_path)

            # If someone provides a --roles-path at the command line, we assume this is
            # for use with a legacy role and we want to maintain backwards compat
            if getattr(options, 'roles_path', None):
                log.warn('Assuming content is of type "role" since --role-path was used')
                _option_role_paths = []
                for role_path in options.roles_path:
                    _option_role_paths.append(role_path)

            # if a server was provided via cli, prepend it to the server list
            if getattr(options, 'server_url', None):
                cli_server = {'url': options.server_url}

                ignore_certs = options.ignore_certs or False
                cli_server['ignore_certs'] = ignore_certs

                _servers = [cli_server]

        # list of dicts with 'name' and 'content_path' items
        # cli --content-paths is hight priority, then --role-path, then configured content-paths
        raw_content_roots = _option_content_paths + _option_role_paths + content_roots_from_config[:]

        log.debug('raw_content_roots: %s', raw_content_roots)
        content_roots = [os.path.expanduser(p) for p in raw_content_roots]

        # list of dicts of url, ignore_certs, token keys
        servers = _servers + servers_from_config[:]

        inst = cls(content_roots=content_roots, servers=servers)

        return inst

    def __repr__(self):
        return 'GalaxyContext(content_path=%s, server=%s)' % \
            (self.content_path, self.server)
