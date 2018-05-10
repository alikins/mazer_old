
from ansible_galaxy import exceptions


class ContentType(object):
    def __init__(self):
        # ie, 'module' or 'strategy_plugin' or 'role'
        self.name = None

        # ie, 'library', or 'strategy_plugins' or 'roles' or 'playbooks'
        self.install_dir_name = None

        # ie, roles require 'meta/main.yml'
        self.requires_meta_main = None

        # if the content type potentially includes other types of content
        # possibly in a subdir in the archive.
        # ie, a 'role' can bundle content, so this is True for roles.
        # 'all', 'role', 'playbook', 'apb', etc: can_bundle_content = True
        # NOTE: it's a fuzzy line, since a content of type 'module' would
        #  be can_bundle_content=False, but it could still have multiple modules in it
        # (but not say, a callback_plugin)

        self.can_bundle_content = False


# TODO: model for the data in a ansible-galaxy.yml in a galaxy content repo
class ContentRepoGalaxyMetadata(object):
    _top_level_fields = ('meta_version',
                         'namespace',
                         'repo_name')

    _supported_versions = ('0.1')

    def __init__(self,
                 meta_version,
                 namespace,
                 repo_name,
                 content_map=None):
        self.meta_version = meta_version
        self.namespace = namespace
        self.repo_name = repo_name
        self.content_map = content_map or {}

    # kind of blurring line between model and serializer, but alas...
    @classmethod
    def from_dict(cls, data):
        meta_version = data['meta_version']

        # TODO: compare versions
        if meta_version not in cls._supported_versions:
            raise exceptions.GalaxyClientError('Version of content repo galaxy metadata (%s) is not supported' % meta_version)

        # NOTE: this doesnt enforce that a content_map key is in CONTENT_PLUGIN_TYPES
        #       should it?
        content_map = {}
        for key in data:
            if key not in cls._top_level_fields:
                content_map[key] = data[key]

        instance = cls(meta_version,
                       data['namespace'],
                       data['repo_name'],
                       content_map)

        return instance

    @property
    def data(self):
        _data = {}
        _data.update(self.content_map)
        _data.update({'meta_version': self.meta_version,
                      'namespace': self.namespace,
                      'repo_name': self.reponame})
        return _data


# ie, the data written to a .galaxy_install_info file
class GalaxyInstallInfo(object):
    def __init__(self):
        # a version string/text
        self.version = None

        # a date and time as a string
        # The default however is based on strftime('%c'), which is locale dependent
        # but we dont know the locale...
        self.install_date = None

    @classmethod
    def from_dict(cls, data):
        return cls(data['version'],
                   data['install_date'])

    @property
    def data(self):
        return {'version': self.version,
                'install_date': self.install_date}


class InstallableContent(object):
    def __init__(self,
                 content_meta=None,
                 content_type=None,
                 archive_to_install=None,
                 # A list of each file to extract, including the archive member name
                 # and the to-be-installed-rel-path-from-content-meta-content-dir
                 file_install_info=None,
                 ):

        # GalaxyContentMeta instance
        self.content_meta = content_meta

        # an instance of models.ContentType
        self.content_type = content_type

        # a tarfile.TarFile instance  (or maybe some wrapper type)
        self.archive_to_install = archive_to_install

        # a map of member.name-in-archive to content-rool-rel-path-to-be-installed-as
        # probably a list of tuples to enfore ordering
        # Should be only the files to install
        self.file_install_file = file_install_info or []
