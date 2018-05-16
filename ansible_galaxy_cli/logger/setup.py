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

DEFAULT_LOGGING_CONFIG_YAML = os.path.expandvars(os.path.expanduser('~/.ansible/galaxy-logging.yml'))

DEFAULT_LOGGING_CONFIG = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        # skip the date for console log handler, but include it for the file log handler
        'console_verbose': {
            'format': DEFAULT_DEBUG_FORMAT,
            'datefmt': '%H:%M:%S',
        },
        'file_verbose': {
            'format': '[%(asctime)s %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
        },
    },

    'filters': {},

    'handlers': {
        'console': {
            'level': DEFAULT_CONSOLE_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'console_verbose',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'level': DEFAULT_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),
            'formatter': 'file_verbose',
        },
        'http_file': {
            'level': DEFAULT_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli-http.log')),
            'formatter': 'file_verbose',

        }
    },

    'loggers': {
        'ansible_galaxy': {
            'handlers': DEFAULT_HANDLERS,
            'level': 'DEBUG',
        },
        'ansible_galaxy.flat_rest_api': {
            'level': 'DEBUG',
        },
        'ansible_galaxy.flat_rest_api.content': {
            'level': 'DEBUG'
        },
        'ansible_galaxy.flat_rest_api.api.(http)': {
            'level': 'INFO',
            'handlers': DEFAULT_HANDLERS,
            # to log verbose debug level logging to http_file handler:
            # 'level': 'DEBUG',
            # 'handlers': ['http_file'],
        },
        'ansible_galaxy.archive.(extract)': {
            'level': 'INFO',
        },
        'ansible_galaxy_cli': {
            'handlers': DEFAULT_HANDLERS,
            'level': 'DEBUG'
        },
    }
}


class ExpandTildeWatchedFileHandler(logging.handlers.WatchedFileHandler):
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


def setup_default():
    logging_config = DEFAULT_LOGGING_CONFIG

    try:
        with open(DEFAULT_LOGGING_CONFIG_YAML, 'r') as logging_config_file:
            logging_config = yaml.safe_load(logging_config_file)
    except Exception as e:
        print(e)
        raise

    return setup(logging_config)
