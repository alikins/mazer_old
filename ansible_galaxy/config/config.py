import collections
import logging

from ansible_galaxy.config import defaults
from ansible_galaxy.config import config_file

log = logging.getLogger(__name__)


class Config(object):
    def __init__(self):
        self.defaults = {}
        self.servers = []
        self.content_roots = []
        self.options = {}

    def as_dict(self):
        return {
            'defaults': self.defaults,
            'servers': self.servers,
            'content_roots': self.content_roots,
            'options': self.options,
        }

    @classmethod
    def from_dict(cls, data):
        inst = cls()
        inst.defaults = data.get('defaults', inst.defaults)
        inst.servers = data.get('servers', inst.servers)
        inst.content_roots = data.get('content_roots', inst.content_roots)
        inst.options = data.get('options', inst.options)
        return inst


def load(full_file_path):
    '''Load the yaml config file at full_file_path and create and return an instance of Config'''
    config_file_data = config_file.load(full_file_path)

    _default_conf_data = collections.OrderedDict(defaults.DEFAULTS)

    config_data = config_file_data or _default_conf_data

    log.debug('config_data: %s', config_data)

    return Config.from_dict(config_data)


def save(config_obj, full_file_path):
    '''Save an instance of Config (config_obj) to full_file_path'''

    config_data = config_obj.as_dict()

    return config_file.save(config_data, full_file_path)
