"""Setup default logging"""

import logging
import logging.config
import os
import yaml

LOG_FILE = os.path.expandvars(os.path.expanduser('~/.ansible/galaxy-cli.log'))

DEFAULT_CONSOLE_LEVEL = os.getenv('GALAXY_CLI_LOG_LEVEL', 'WARNING').upper()
DEFAULT_LEVEL = 'DEBUG'

DEFAULT_DEBUG_FORMAT = '[%(asctime)s,%(msecs)03d %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s'
# DEFAULT_HANDLERS = ['console', 'file']
DEFAULT_HANDLERS = ['file']

DEFAULT_LOGGING_CONFIG_YAML = os.path.join(os.path.dirname(__file__), 'default-galaxy-logging.yml')
LOGGING_CONFIG_YAML = os.path.expandvars(os.path.expanduser('~/.ansible/galaxy-logging.yml'))

FALLBACK_LOGGING_CONFIG = {
    'version': 1,

    'disable_existing_loggers': False,

    'handlers': {
        'null_handler': {
            'class': 'logging.NullHandler',
            'level': 'ERROR',
        },
    },

    'loggers': {
        'ansible_galaxy': {
            'handlers': ['null_handler'],
            'level': 'INFO',
        },
        'ansible_galaxy_cli': {
            'handlers': ['null_handler'],
            'level': 'INFO',
        },
    }
}


class ExpandTildeWatchedFileHandler(logging.handlers.WatchedFileHandler):
    '''A variant of WatchedFileHandler that will expand ~/ in it's filename param'''
    def __init__(self, *args, **kwargs):
        orig_filename = kwargs.pop('filename', '~/.ansible/ansible-galaxy-cli.log')
        kwargs['filename'] = os.path.expandvars(os.path.expanduser(orig_filename))
        super(ExpandTildeWatchedFileHandler, self).__init__(*args, **kwargs)


def setup(logging_config=None):
    logging_config = logging_config or {}

    conf = logging.config.dictConfig(logging_config)

    # import logging_tree
    # logging_tree.printout()

    return conf


def load_config_yaml(config_file_path):
    logging_config = None

    try:
        with open(config_file_path, 'r') as logging_config_file:
            logging_config = yaml.safe_load(logging_config_file)
    except OSError as e:
        pass
    except yaml.YamlError as e:
        print(e)

    return logging_config


def setup_default():
    logging_config = None

    # load custom logging config
    logging_config = load_config_yaml(LOGGING_CONFIG_YAML)

    # if there is no custom config, load the default
    if not logging_config:
        logging_config = load_config_yaml(DEFAULT_LOGGING_CONFIG_YAML)

    # fallback is basically no setup, null handler, etc
    if not logging_config:
        logging_config = FALLBACK_LOGGING_CONFIG

    return setup(logging_config)
