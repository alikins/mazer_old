########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
# (C) 2018, Adam Miller <admiller@redhat.com>
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

import datetime
import errno
import fnmatch
import logging
import os
from shutil import rmtree
import tarfile
import yaml

from ansible_galaxy.config import defaults
from ansible_galaxy import exceptions
from ansible_galaxy import archive
from ansible_galaxy.fetch.scm_url import ScmUrlFetch
from ansible_galaxy.fetch.local_file import LocalFileFetch
from ansible_galaxy.fetch.remote_url import RemoteUrlFetch
from ansible_galaxy.fetch.galaxy_url import GalaxyUrlFetch
from ansible_galaxy.models.content import CONTENT_PLUGIN_TYPES, CONTENT_TYPES
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP, TYPE_DIR_CONTENT_TYPE_MAP
from ansible_galaxy.models import content
from ansible_galaxy.utils.yaml_parse import yaml_parse


log = logging.getLogger(__name__)

# has a GalaxyContentMeta FIXME: rename back to GalaxyContentData
# FIXME: erk, and a metadata (ie, ansible-galaxy.yml)
#
# can provide a ContentInstallInfo


# FIXME: do we have an enum like class for py2.6? worth a dep?
class FetchMethods(object):
    SCM_URL = 'SCM_URL'
    LOCAL_FILE = 'LOCAL_FILE'
    REMOTE_URL = 'REMOTE_URL'
    GALAXY_URL = 'GALAXY_URL'


def choose_content_fetch_method(scm_url=None, src=None):
    log.debug('scm_url=%s, src=%s', scm_url, src)
    if scm_url:
        # create tar file from scm url
        return FetchMethods.SCM_URL

    if not src:
        raise exceptions.GalaxyClientError("No valid content data found")

    if os.path.isfile(src):
        # installing a local tar.gz
        return FetchMethods.LOCAL_FILE

    if '://' in src:
        return FetchMethods.REMOTE_URL

    # if it doesnt look like anything else, assume it's galaxy
    return FetchMethods.GALAXY_URL


#        fetch_method = ScmUrlFetch(scm_url=scm_url, scm_spec=spec)
#        return fetch_method

# FIXME: really just three methods here, install, remove, fetch. install -> save, fetch -> load
#       remove -> delete
class GalaxyContent(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')
    NO_META = ('module', 'strategy_plugin')

    # FIXME(alikins): Not a fan of vars/args with names like 'type', but leave it for now
    def __init__(self, galaxy, name,
                 src=None, version=None, scm=None, path=None, type="role",
                 display_callback=None):
        """
        The GalaxyContent type is meant to supercede the old GalaxyRole type,
        supporting all Galaxy Content Types as per the Galaxy Repository Metadata
        specification.

        The "content_type" is default to "role" in order to maintain backward
        compatibility as a drop-in replacement for GalaxyRole

        :param galaxy: Galaxy object from ansible.galaxy
        :param name: str, name of Galaxy Content desired
        :kw src: str, source uri
        :kw version: str, version required/requested
        :kw scm: str, scm type
        :kw path: str, local path to Galaxy Content
        :kw content_type: str, Galaxy Content type
        """

        content_type = type

        self._metadata = None
        # TODO: replace with empty ContentRepository instance?
        self._galaxy_metadata = {}
        self._install_info = None
        self._validate_certs = not galaxy.options.ignore_certs

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.log.debug('Validate TLS certificates: %s', self._validate_certs)

        self.display_callback = display_callback or self._display_callback

        self.options = galaxy.options
        self.galaxy = galaxy

        self.content_meta = content.GalaxyContentMeta(name=name, src=src, version=version,
                                                      scm=scm, path=path, content_type=content_type,
                                                      content_dir=CONTENT_TYPE_DIR_MAP.get(content_type, None))

        # TODO: remove this when the data constructors are split
        # This is a marker needed to make certain decisions about single
        # content type vs all content found in the repository archive when
        # extracting files
        self._install_all_content = False
        if content_type == "all":
            self._install_all_content = True

        self._set_type(content_type)

        if content_type not in CONTENT_TYPES and content_type != "all":
            raise exceptions.GalaxyClientError("%s is not a valid Galaxy Content Type" % content_type)

        # Set original path, needed to determine what action to take in order to
        # maintain backwards compat with legacy roles
        self._orig_path = path

        # Set self.path and self.path_dir
        self._set_content_paths(path)

    def _display_callback(self, *args, **kwargs):
        level_arg = kwargs.pop('level', None)
        levels = {'warning': 'WARNING'}
        level = levels.get(level_arg, None)
        if level:
            print('%s' % level, *args)
        print(*args)

    def __repr__(self):
        """
        Returns "content_name (version) content_type" if version is not null
        Returns "content_name content_type" otherwise
        """
        if self.version:
            return "%s (%s) %s" % (self.content_meta.name, self.version, self.content_type)
        else:
            return "%s %s" % (self.content_meta.name, self.content_type)

    def __eq__(self, other):
        return self.content_meta.name == other.content_meta.name

    def _set_type(self, new_type):
        """
        Set the internal type information, because GalaxyContent can contain
        many different types this needs to be able to change state depending on
        content installation.

        This will update:
            self.content_type
            self.type_dir

        :param new_type: str, new content_type to assign
        """

        # FIXME - Anytime we change state like this, it feels wrong. Should
        #         probably evaluate a better way to do this.
        self.content_type = new_type

        # We need this because the type_dir inside a Galaxy Content archive is
        # not the same as it's installed location as per the CONTENT_TYPE_DIR_MAP
        # for some types
        self.type_dir = "%ss" % new_type

    # FIXME: just build a new GalaxyContentMeta and replace
    def _set_content_paths(self, path=None):
        """
        Conditionally set content path based on content type
        """
        self.log.debug('content_meta before: %s', self.content_meta)
        new_path_info = self._get_content_paths(path, content_type=self.content_type,
                                                content_name=self.content_meta.name,
                                                galaxy_content_paths=self.galaxy.content_paths[:],
                                                install_all_content=self._install_all_content)
        self.log.debug('XXXXXXXXXXXXXXX new_path_info=%s', new_path_info)
        # FIXME: remove all the internal state tweaking
        # self.path is a property that returns self.content_meta.path
        self.content_meta.path = new_path_info['content_path']
        self.paths = new_path_info['content_paths']
        # FIXME: what is the diff between self.path and self.content_meta.path ?
        self.content_meta.path = new_path_info['content_content_path']
        self.galaxy.content_paths = new_path_info['galaxy_content_paths']
        self.content_type = new_path_info['content_type']
        self._install_all_content = new_path_info['install_all_content']
        self.log.debug('content_meta after: %s', self.content_meta)

    def _get_content_paths(self, path=None, content_name=None, content_type=None,
                           galaxy_content_paths=None,
                           content_content_path=None,
                           install_all_content=None):
        """
        Return a tuple of content path info

        returns (content_path, content_paths, galaxy_content_path,
                 content_type, install_all_content, content_content_path)
        """
        content_paths = ""  # FIXME - handle multiple content types here
        content_path = None
        content_content_path = content_content_path
        new_content_type = content_type
        # FIXME: cp for now, will need to pass in value
        galaxy_content_paths = galaxy_content_paths or []
        install_all_content = install_all_content or False

        # FIXME - ":" is a placeholder default value for --content_path in the
        #         galaxy cli and it should really not be
        if path is not None and path != ":":
            # "all" doesn't actually exist, but it's an internal idea that means
            # "we're going to install everything", however that comes with the
            # caveot of needing to inspect to find out if there's a meta/main.yml
            # and handling a legacy role type accordingly

            self.log.debug('old path=%s', path)

            if content_name not in path and new_content_type in ["role", "all"]:
                path = os.path.join(path, content_name)

            self.log.debug('new path=%s', path)

            # self.path = path
            content_path = path

            # We need for first set self.path (as we did above) in order to then
            # allow the property function "metadata" to check for the existence
            # of a meta/main.yml and it not, then we don't join the name to the
            # end of the path because it's not necessary for non-role content
            # types as they aren't namespaced by directory
            if not self.metadata:
                content_path = path
            else:
                # If we find a meta/main.yml, this is a legacy role and we need
                # to handle it
                new_content_type = 'role'
                # self._set_type("role")
                # self._install_all_content = False
                install_all_content = False

            content_paths = [content_path]
        else:
            # First, populate the self.galaxy.content_paths for processing below

            # Unfortunately this exception is needed and we can't easily rely
            # on the dir_map because there's not consistency of plural vs
            # singular of type between the contants vars read in from the config
            # file and the subdirectories
            if new_content_type != "all":
                # self.log.debug('ctdm: %s', json.dumps(CONTENT_TYPE_DIR_MAP, indent=4))
                galaxy_content_paths = [os.path.join(os.path.expanduser(p),
                                                     CONTENT_TYPE_DIR_MAP[new_content_type]) for p in defaults.DEFAULT_CONTENT_PATH]
            else:
                galaxy_content_paths = [os.path.expanduser(p) for p in defaults.DEFAULT_CONTENT_PATH]

            # use the first path by default
            if new_content_type == "role":
                content_content_path = os.path.join(galaxy_content_paths[0], content_name)
            else:
                content_content_path = galaxy_content_paths[0]
            # create list of possible paths
            content_paths = [x for x in galaxy_content_paths]
            content_paths = [os.path.join(x, content_name) for x in content_paths]

        result = {'content_path': content_path,
                  'content_paths': content_paths,
                  'galaxy_content_paths': galaxy_content_paths,
                  'content_type': new_content_type,
                  'install_all_content': install_all_content,
                  'content_content_path': content_content_path}

        log.debug('get_content_path results=%s', result)

        return result

    # FIXME: update calling code instead?
    @property
    def name(self):
        return self.content_meta.name

    @property
    def version(self):
        return self.content_meta.version

    @property
    def src(self):
        return self.content_meta.src

    @property
    def scm(self):
        return self.content_meta.scm

    @property
    def content_dir(self):
        return self.content_meta.content_dir

    @property
    def path(self):
        return self.content_meta.path

    @property
    def metadata(self):
        """
        Returns role metadata for type role, errors otherwise
        """
        if self.content_type in ["role", "all"]:
            if self._metadata is None:
                meta_path = os.path.join(self.content_meta.path, self.META_MAIN)
                if os.path.isfile(meta_path):
                    try:
                        f = open(meta_path, 'r')
                        self._metadata = yaml.safe_load(f)
                    except Exception as e:
                        self.log.exception(e)
                        self.log.debug("Unable to load metadata for %s", self.content_meta.name)
                        return False
                    finally:
                        f.close()

            return self._metadata
        else:
            return {}

    # TODO: class/module for ContentInstallInfo
    @property
    def install_info(self):
        """
        Returns Galaxy Content install info
        """
        # FIXME: Do we want to have this for galaxy content?
        if self._install_info is None:

            info_path = os.path.join(self.path, self.META_INSTALL)
            if os.path.isfile(info_path):
                try:
                    f = open(info_path, 'r')
                    self._install_info = yaml.safe_load(f)
                except Exception as e:
                    self.log.exception(e)
                    self.debug("Unable to load Galaxy install info for %s", self.content_meta.name)
                    return False
                finally:
                    f.close()
        return self._install_info

    # FIXME: should probably be a GalaxyInfoInfo class
    def _write_galaxy_install_info(self):
        """
        Writes a YAML-formatted file to the role's meta/ directory
        (named .galaxy_install_info) which contains some information
        we can use later for commands like 'list' and 'info'.
        """
        # FIXME - unsure if we want this, need to figure it out and if we want it then need to handle
        #

        info = dict(
            version=self.version,
            install_date=datetime.datetime.utcnow().strftime("%c"),
        )
        if not os.path.exists(os.path.join(self.path, 'meta')):
            os.makedirs(os.path.join(self.path, 'meta'))
        info_path = os.path.join(self.path, self.META_INSTALL)
        with open(info_path, 'w+') as f:
            # FIXME: just return the install_info dict (or better, build it elsewhere and pass in)
            # FIXME: stop minging self state
            try:
                self._install_info = yaml.safe_dump(info, f)
            except Exception as e:
                self.log.warn('unable to serialize .galaxy_install_info to info_path=%s for data=%s', info_path, info)
                self.log.exception(e)
                return False

        return True

    # FIXME: persisting of content archives or subsets thereof
    # FIXME: currently does way too much, could be split into generic and special case classes
    # FIXME: some weirdness here is caused by tarfile API being a little strange. To extract a file
    #        to a different path than from the archive, you have to update each TarInfo member and
    #        change it's 'name' attribute after loading/opening a TarFile() but before extract()
    #        Since it's mutating the TarFile object, have to be careful if anything will use the object
    #        after it was changed
    def _write_archived_files(self, tar_file, parent_dir,
                              file_name=None, files_to_extract=None,
                              extract_to_path=None):
        """
        Extract and write out files from the archive, this is a common operation
        needed for both old-roles and new-style galaxy content, the main
        difference is parent directory

        :param tar_file: tarfile, the local archive of the galaxy content files
        :param parent_dir: str, parent directory path to extract to
        :kwarg file_name: str, specific filename to extract from parent_dir in archive
        """
        # now we do the actual extraction to the path
        self.log.debug('tar_file=%s, parent_dir=%s, file_name=%s', tar_file, parent_dir, file_name)
        self.log.debug('extract_to_path=%s', extract_to_path)

        import traceback
        traceback.print_stack()

        files_to_extract = files_to_extract or []
        plugin_found = None

        if file_name:
            files_to_extract.append(file_name)
        # self.log.debug('files_to_extract: %s', files_to_extract)

        path = extract_to_path or self.path
        self.log.debug('path=%s', path)

        # do we need to drive this from tar_file members if we have file_names_to_extract?
        # for member in tar_file.getmembers():
        for member in files_to_extract:
            # Have to preserve this to reset it for the sake of processing the
            # same TarFile object many times when handling an ansible-galaxy.yml
            # file
            orig_name = member.name
            # self.log.debug('member.name=%s', member.name)
            # self.log.debug('member=%s, orig_name=%s, member.isreg()=%s member.issym()=%s',
            #               member, orig_name, member.isreg(), member.issym())
            # we only extract files, and remove any relative path
            # bits that might be in the file for security purposes
            # and drop any containing directory, as mentioned above
            # TODO: could we use tar_info_content_name_match with a '*' patter here to
            #       get a files_to_extract?
            if member.isreg() or member.issym():
                parts_list = member.name.split(os.sep)

                # self.log.debug('content_type: %s', self.content_type)
                # filter subdirs if provided
                if self.content_type != "role":
                    # Check if the member name (path), minus the tar
                    # archive baseir starts with a subdir we're checking
                    # for
                    # self.log.debug('parts_list: %s', parts_list)
                    # self.log.debug('parts_list[1]: %s', parts_list[1])
                    # self.log.debug('CONTENT_TYPE_DIR_MAP[self.content_type]: %s', CONTENT_TYPE_DIR_MAP[self.content_type])
                    if file_name:
                        # The parent_dir passed in when a file name is specified
                        # should be the full path to the file_name as defined in the
                        # ansible-galaxy.yml file. If that matches the member.name
                        # then we've found our match.
                        if member.name == os.path.join(parent_dir, file_name):
                            # lstrip self.content_meta.name because that's going to be the
                            # archive directory name and we don't need/want that
                            plugin_found = parent_dir.lstrip(self.content_meta.name)

                    elif len(parts_list) > 1 and parts_list[1] == CONTENT_TYPE_DIR_MAP[self.content_type]:
                        plugin_found = CONTENT_TYPE_DIR_MAP[self.content_type]

                    # self.log.debug('plugin_found1: %s', plugin_found)
                    if not plugin_found:
                        continue

                # self.log.debug('parts_list: %s', parts_list)
                # self.log.debug('plugin_found2: %s', plugin_found)
                if plugin_found:
                    # If this is not a role, we don't expect it to be installed
                    # into a subdir under roles path but instead directly
                    # where it needs to be so that it can immediately be used
                    #
                    # FIXME - are galaxy content types namespaced? if so,
                    #         how do we want to express their path and/or
                    #         filename upon install?
                    if plugin_found in parts_list:
                        # subdir_index = parts_list.index(plugin_found) + 1
                        subdir_index = parts_list.index(plugin_found) + 1
                        # self.log.debug('subdir_index: %s parts_list[subdir_index:]=%s', subdir_index, parts_list[subdir_index:])
                        parts = parts_list[subdir_index:]
                    else:
                        # The desired subdir has been identified but the
                        # current member belongs to another subdir so just
                        # skip it
                        continue
                else:
                    parts = member.name.replace(parent_dir, "", 1).split(os.sep)
                    # self.log.debug('plugin_found falsey, building parts: %s', parts)

                # self.log.debug('parts: %s', parts)
                final_parts = []
                for part in parts:
                    if part != '..' and '~' not in part and '$' not in part:
                        final_parts.append(part)
                member.name = os.path.join(*final_parts)
                # self.log.debug('final_parts: %s', final_parts)
                self.log.debug('member.name: %s', member.name)

                if self.content_type in CONTENT_PLUGIN_TYPES:
                    self.display_callback(
                        "-- extracting %s %s from %s into %s" %
                        (self.content_type, member.name, self.content_meta.name, os.path.join(path, member.name))
                    )
                if os.path.exists(os.path.join(path, member.name)) and not getattr(self.options, "force", False):
                    if self.content_type in CONTENT_PLUGIN_TYPES:
                        message = (
                            "the specified Galaxy Content %s appears to already exist." % os.path.join(path, member.name),
                            "Use of --force for non-role Galaxy Content Type is not yet supported"
                        )
                        if self._install_all_content:
                            # FIXME - Probably a better way to handle this
                            self.display_callback(" ".join(message), level='warning')
                        else:
                            raise exceptions.GalaxyClientError(" ".join(message))
                    else:
                        message = "the specified role %s appears to already exist. Use --force to replace it." % self.content_meta.name
                        if self._install_all_content:
                            # FIXME - Probably a better way to handle this
                            self.display_callback(message, level='warning')
                        else:
                            raise exceptions.GalaxyClientError(message)

                # Alright, *now* actually write the file
                self.log.debug('Extracting member=%s, path=%s', member, path)
                tar_file.extract(member, path)

                # Reset the name so we're on equal playing field for the sake of
                # re-processing this TarFile object as we iterate through entries
                # in an ansible-galaxy.yml file
                member.name = orig_name

        if self.content_type != "role" and self.content_type not in self.NO_META:
            if not plugin_found:
                raise exceptions.GalaxyClientError("Required subdirectory not found in Galaxy Content archive for %s" % self.content_meta.name)

    def remove(self):
        """
        Removes the specified content from the content path.
        There is a sanity check to make sure there's a meta/main.yml or
        ansible-galaxy.yml file at this path so the user doesn't blow away
        random directories.
        """
        # FIXME - not yet implemented for non-role types
        if self.content_type == "role":
            if self.metadata:
                try:
                    rmtree(self.path)
                    return True
                except Exception as e:
                    self.log.warn('unable to rmtree for path=%s', self.path)
                    self.log.exception(e)
                    pass

        else:
            raise exceptions.GalaxyClientError("Removing Galaxy Content not yet implemented")

        return False

    def _build_download_url(self, src, external_url=None, version=None):
        if external_url and version:
            archive_url = '%s/archive/%s.tar.gz' % (external_url, version)
            return archive_url

        archive_url = src

        return archive_url

    # FIXME: can remove, dont think it is used
    def _install_all_old_way(self,
                             content_tar_file,
                             archive_parent_dir,
                             members,
                             install_all_content):

        installed = False
        # FIXME: extract and test, build a map of the name transforms first, then apply, then install
        # Find out what plugin type subdirs exist in this repo
        #
        # This list comprehension will iterate every member entry in
        # the tarfile, split it's name by os.sep and drop the top most
        # parent dir, which will be self.content_meta.name (we don't want it as it's
        # not needed for plugin types. First make sure the length of
        # that split and drop of parent dir is length > 1 and verify
        # that the subdir is infact in CONTENT_TYPE_DIR_MAP.values()
        #
        # This should give us a list of valid content type subdirs
        # found heuristically within this Galaxy Content repo
        #
        plugin_subdirs = [
            os.path.join(m.name.split(os.sep)[1:])[0]
            for m in members
            if len(os.path.join(m.name.split(os.sep)[1:])) > 1
            and os.path.join(m.name.split(os.sep)[1:])[0] in CONTENT_TYPE_DIR_MAP.values()
        ]

        self.log.debug('plugin_subdirs: %s', plugin_subdirs)
        if plugin_subdirs:


            # FIXME: stop munging state
            self._install_all_content = True


            for plugin_subdir in plugin_subdirs:
                # Set the type, this is neccesary for processing extraction of
                # the tarball content
                #
                # rstrip the letter 's' from the plugin type subdir, this should
                # be the type
                self._set_type(plugin_subdir.rstrip('s'))
                self._set_content_paths(None)
                self._write_archived_files(content_tar_file, archive_parent_dir)
                installed = True
        else:
            raise exceptions.GalaxyClientError("This Galaxy Content does not contain valid content subdirectories, expected any of: %s "
                                               % CONTENT_TYPES)

        return installed

    def _install_all(self, content_tar_file, archive_parent_dir):
        # FIXME: not sure of best approach/pattern to figuring out how/where to extract the content too
        #        It is almost similar to a url rewrite engine. Or really, persisting of some object that was loaded from a DTO
        member_matches = archive.filter_members_by_content_type(content_tar_file, self.content_meta)

        # self.log.debug('member_matches: %s' % member_matches)
        self.log.debug('content_meta: %s', self.content_meta)
        self.log.info('about to extract %s to %s', self.content_meta.name, self.content_meta.path)

        archive.extract_by_content_type(content_tar_file,
                                        archive_parent_dir,
                                        self.content_meta,
                                        files_to_extract=member_matches,
                                        extract_to_path=self.content_meta.path,
                                        content_type_requires_meta=True)

        installed = True
        return installed

# install
# - fetch the content_archive
# - open the content archive
# - search for any 'meta/main.yml' files in archive
#   - and figure out 'archive_parent_dir'
# - hack to mutate content_path state
# - try to find archive_parent_dir even harder
#   - for the 'no ansible-galaxy.yml' case
# - lookup for meta/main.yml again
#   - and/or lookup for ansible-galaxy.yml and load it
# - while loop around a handful of ways to figure out what/where to install
#  - handle content_type='all'
#  - handle old style role content (meta/main.yml, no ansible-galaxy.yml)
#  - or - do ansible-galaxy.yml stuff
#  - or for no meta/main.yml and no ansible-galaxy.yml
#     - for not 'all' or specific content_types, do an extract
#     - unused way to handle 'all' content type based on path munging
#     - if something 'installed', break
#     - else wraise install method error

    # TODO: split this up, it's pretty gnarly
    def install(self):
        # TODO: some useful exceptions for 'cant find', 'cant read', 'cant write'
        fetch_method = choose_content_fetch_method(scm_url=self.scm, src=self.src)

        fetcher = None
        if fetch_method == FetchMethods.SCM_URL:
            fetcher = ScmUrlFetch(scm_url=self.scm, scm_spec=self.spec)
        elif fetch_method == FetchMethods.LOCAL_FILE:
            # the file is a tar, so open it that way and extract it
            # to the specified (or default) content directory
            fetcher = LocalFileFetch(self.src)
        elif fetch_method == FetchMethods.REMOTE_URL:
            fetcher = RemoteUrlFetch(remote_url=self.src, validate_certs=self._validate_certs)
        elif fetch_method == FetchMethods.GALAXY_URL:
            fetcher = GalaxyUrlFetch(content_spec=self.src,
                                     content_version=self.version,
                                     galaxy_context=self.galaxy,
                                     validate_certs=self._validate_certs)
        else:
            raise exceptions.GalaxyError('No approriate content fetcher found for %s %s',
                                         self.scm, self.src)

        self.log.debug('fetch_method: %s', fetch_method)

        if fetcher:
            content_archive = fetcher.fetch()
            self.log.debug('content_archive=%s', content_archive)

        if not content_archive:
            raise exceptions.GalaxyClientError('No valid content data found for %s', self.src)

        # FIXME: the 'fetch', persist locally,  and 'install' steps should not be combined here
        # FIXME: mv to own method[s], unindent
        # if content_archive:

        self.log.debug("installing from %s", content_archive)

        # FIXME: unindent the non error else here
        if not tarfile.is_tarfile(content_archive):
            raise exceptions.GalaxyClientError("the file downloaded was not a tar.gz")

        if content_archive.endswith('.gz'):
            content_tar_file = tarfile.open(content_archive, "r:gz")
        else:
            content_tar_file = tarfile.open(content_archive, "r")
        # verify the role's meta file

        meta_file = None
        archive_parent_dir = None
        members = content_tar_file.getmembers()

        (meta_file, meta_parent_dir, galaxy_file, archive_parent_dir) = \
            archive.find_archive_metadata(members)

        # import pprint
        # self.log.debug('content_archive (%s) members: %s', content_archive, pprint.pformat(members))
        # next find the metadata file

        # FIXME: mv to method or ditch entirely and drive from a iterable of files to extract and save
        # FIXME: this is role specific logic so could move elsewhere

        # self.log.debug('self.content_type: %s', self.content_type)

        # content types like 'module' shouldn't care about meta_file elsewhere
        if self.content_type in self.NO_META:
            meta_file = None

        # FIXME: THIS IS A HACK
        #
        # We've determined that this is a legacy role, we're going to
        # change state and re-eval paths for backwards compat with the
        # legacy role type
        if self.content_type == "all" and meta_file:
            self._set_type("role")
            self._set_content_paths(self._orig_path)
            self._install_all_content = False

        # FIXME: mv to it's own method
        if not archive_parent_dir:
            archive_parent_dir = archive.find_archive_parent_dir(members, self.content_meta)

        self.log.debug("meta_file: %s galaxy_file: %s self.content_type: %s", meta_file, galaxy_file, self.content_type)
        self.log.debug("archive_parent_dir: %s", archive_parent_dir)
        self.log.debug("meta_parent_dir: %s", meta_parent_dir)

        if not meta_file and not galaxy_file and self.content_type == "role":
            raise exceptions.GalaxyClientError("this role does not appear to have a meta/main.yml file or ansible-galaxy.yml.")

        # FIXME: mv to AnsibleGalaxyMetadata
        self._galaxy_metadata, self._metadata = archive.load_archive_metadata(content_tar_file,
                                                                              galaxy_file,
                                                                              meta_file)

        # we strip off any higher-level directories for all of the files contained within
        # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
        # hand, does not have a parent directory at all.

        if not os.path.isdir(self.content_meta.path):
            self.log.debug('No content path (%s) found so creating it', self.content_meta.path)
            os.makedirs(self.content_meta.path)

        installed = False

        # FIXME: get rid of the while loop or continue if nothing catches
        # TODO: need an install state machine real bad
        while not installed:
            if self.content_type != "all":
                self.display_callback("- extracting %s %s to %s" % (self.content_type, self.content_meta.name, self.path))
            else:
                self.display_callback("- extracting all content in %s to content directories" % self.content_meta.name)

            # FIXME: a few pages of code in a try block, extract to own method/class
            self.log.info('Installing content of type: %s', self.content_meta.content_type)
            self.log.debug('self.content_type=%s, self.content_meta.content_type=%s, are_equal? %s',
                           self.content_type, self.content_meta.content_type,
                           self.content_type == self.content_meta.content_type)

            # TODO: truthiness of _galaxy_metadata may be better, since that means it was parsed and non empty
            if galaxy_file:
                self.log.info('Installing %s as a content_type=%s', self.content_meta.name, self.content_meta.content_type)

                self.log.debug('galaxy_file=%s', galaxy_file)

                import pprint
                self.log.debug('galaxy_metadata=%s', pprint.pformat(self._galaxy_metadata))
                # Parse the ansible-galaxy.yml file and install things
                # as necessary

                # FIXME - need to handle the scenario where we want
                #         all content types defined in the ansible-galaxy.yml file

                for _content in self._galaxy_metadata:
                    _content_dir = CONTENT_TYPE_DIR_MAP.get(_content, None)
                    _content_type = _content

                    if _content == 'modules':
                        _content_dir = 'library'
                        _content_type = 'module'

                    _content_meta = content.GalaxyContentMeta(name=self.content_meta.name,
                                                              src=self.content_meta.src,
                                                              version=self.content_meta.version,
                                                              scm=self.content_meta.scm,
                                                              path=self.content_meta.path,
                                                              content_type=_content_type,
                                                              content_dir=_content_dir)

                    #if not _content_dir:
                    #    # FIXME - add more types other than module here
                    #    raise exceptions.GalaxyClientError("ansible-galaxy.yml install not yet supported for content_type=%s content_dir=%s" %
                    #                                       (self.content_type, _content_dir))

                    # FIXME: suppose this is basically options for setting up a deserializer
                    # FIXME: def should be elsewhere, likely some serializer class
                    if _content == "meta_version":
                        continue
                    elif _content == "modules":
                        #self._set_type("module")
                        #self._set_content_paths()
                        for module in self._galaxy_metadata[_content]:
                            path_pattern = module['path']
                            self.log.debug('galaxy md modules module=%s', module)
                            self.log.debug('galaxy md modules path_pattern=%s', path_pattern)

                            # FIXME: os.sep seems wrong here, the yaml format shouldn't care?
                            member_matches = archive.filter_members_by_fnmatch(content_tar_file, '*/%s' % path_pattern)

                            # import pprint
                            self.log.debug('member_matches=%s', pprint.pformat(member_matches))

                            self.log.info('about to extract content_type=%s %s to %s',
                                          _content_meta.content_type, _content_meta.name, _content_meta.path)

                            res = archive.extract_by_content_type(content_tar_file,
                                                                  archive_parent_dir,
                                                                  _content_meta,
                                                                  files_to_extract=member_matches,
                                                                  # content_type=self.content_meta.content_type,
                                                                  extract_to_path=_content_meta.path,
                                                                  content_type_requires_meta=False)
                            self.log.debug('res: %s', res)

                            installed = True

                            break


                            # FIXME: on a general level, having content that only sometimes has dep info seems like a problem
                            if 'dependencies' in module:
                                for dep in module['dependencies']:
                                    if 'src' not in dep:
                                        raise exceptions.GalaxyClientError("ansible-galaxy.yml dependencies must provide a src")

                                    dep_content_info = yaml_parse(dep['src'])
                                    # FIXME - Should we assume this to be true for module deps?
                                    dep_content_info["type"] = "module_util"

                                    self.display_callback('- processing dependency: %s' % dep_content_info["src"])

                                    # This is an external dep, treat it as such
                                    if dep_content_info["scm"]:
                                        dep_content = GalaxyContent(self.galaxy, **dep_content_info)
                                        try:
                                            installed = dep_content.install()
                                        except exceptions.GalaxyClientError as e:
                                            self.display_callback("- dependency %s was NOT installed successfully: %s " %
                                                                  (dep_content.name, str(e)), level='warning')
                                            continue
                                    else:
                                        # Local dep, just install it
                                        self._set_type("module_util")
                                        self._set_content_paths()
                                        if len(dep["src"].split(os.sep)) > 1:
                                            if dep["src"].split(os.sep)[-1] in ['/', '*']:
                                                # Handle the glob or designation of entire directory install
                                                self._write_archived_files(content_tar_file, os.path.join(archive_parent_dir, dep['src']))
                                                installed = True
                                            else:
                                                self._write_archived_files(
                                                    content_tar_file,
                                                    os.path.join(archive_parent_dir, os.path.dirname(dep['src'])),
                                                    file_name=dep['src'].split(os.sep)[-1]
                                                )
                                                installed = True

                    else:
                        # FIXME - add more types other than module here
                        raise exceptions.GalaxyClientError("ansible-galaxy.yml install not yet supported for content_type %s" % self.content_type)

            elif self.content_meta.content_type == 'all':
                self.log.info('Installing %s as a content_type=%s', self.content_meta.name, self.content_meta.content_type)

                installed = self._install_all(content_tar_file, archive_parent_dir)

                # write out the install info file for later use
                # self._write_galaxy_install_info()

                break

            elif not meta_file and not galaxy_file:
                self.log.info('Installing %s as a content_type=%s', self.content_meta.name, self.content_meta.content_type)
                # No meta/main.yml found so it's not a legacy role
                # and no galaxyfile found, so assume it's a new
                # galaxy content type and attempt to install it by
                # heuristically walking the directories and install
                # the appropriate things in the appropriate places

                self.log.info('no meta/main.yml found and no ansible-galaxy.yml found')

                # FIXME: this is basically a big switch to decide what serializer to use
                if self.content_type != "all":
                    # TODO: based on content_name, need to find/build the full path to that in the
                    #       tar archive so we can extract it.
                    #       ie, alikins.testing-content.elastic_search.py
                    #       full path would be:
                    #         ansible-testing-content-master/library/database/misc/elasticsearch_plugin.py
                    #       Then we pass that into _write_archive_files as file_name arg

                    # tar info for each file, so we can filter on filename match and file type
                    # tar_file_members = content_tar_file.getmembers()

                    member_matches = archive.filter_members_by_content_type(content_tar_file, self.content_meta)

                    # match_by_content_type() ?
                    # member_matches = [tar_file_member for tar_file_member in tar_file_members
                    #                  if tar_info_content_name_match(tar_file_member,
                    #                                                 "",
                    #                                                 # self.content_meta.name,
                    #                                                 content_path=CONTENT_TYPE_DIR_MAP[self.content_meta.content_type])]

                    self.log.info('about to extract content_type=%s %s to %s',
                                  self.content_meta.content_type, self.content_meta.name, self.content_meta.path)
                    res = archive.extract_by_content_type(content_tar_file,
                                                          archive_parent_dir,
                                                          self.content_meta,
                                                          files_to_extract=member_matches,
                                                          # content_type=self.content_meta.content_type,
                                                          extract_to_path=self.content_meta.path,
                                                          content_type_requires_meta=False)
                    self.log.debug('res: %s', res)
                    installed = True
                else:

                    self.log.debug('No meta/main, no galaxy file, not ct="all"? XXXXXXXXXXXXXX')
                    installed = self._install_all_old_way(content_tar_file,
                                                          archive_parent_dir,
                                                          members,
                                                          self._install_all_content)
            elif installed:
                self.log.debug('installed=%s  breaking out of while', installed)
                break
            else:
                self.log.debug('installed=%s', installed)
                self.log.debug('failed for content_meta=%s self.content_type=%s', self.content_meta, self.content_type)
                raise exceptions.GalaxyClientError('Cant figure out what install method to use')

            # return the parsed yaml metadata
            self.display_callback("- %s was installed successfully to %s" % (str(self), self.path))

            # rm any temp files created when getting the content archive
            fetcher.cleanup()

            return True

        return installed
        # return False

    # TODO: property of GalaxyContentMeta ?
    @property
    def spec(self):
        """
        Returns content spec info
        {
           'scm': 'git',
           'src': 'http://git.example.com/repos/repo.git',
           'version': 'v1.0',
           'name': 'repo'
        }
        """
        return dict(scm=self.scm, src=self.src, version=self.version, name=self.content_meta.name)
