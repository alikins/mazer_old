"""Setup default logging"""

import logging
import logging.config
import os

try:
    import color_debug
except ImportError as e:
    print(e)

LOG_FILE = os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),

#DEFAULT_LEVEL = 'INFO'
DEFAULT_LEVEL = 'DEBUG'

DEFAULT_LOGGING_CONFIG = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        # skip the date for console log handler, but include it for the file log handler
        'console_verbose': {
            'class': color_debug.ColorFormatter,
            'format': '[%(asctime)s,%(msecs)03d %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
            'fmt': '[%(asctime)s,%(msecs)03d %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%H:%M:%S',
            'default_color_by_attr': 'name',
            'auto_color': True
        },
        'file_verbose': {
            'format': '[%(asctime)s %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
        },
    },

    'filters': {},

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console_verbose',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),
            'formatter': 'file_verbose',
        }
    },

    'loggers': {
        'ansible_galaxy': {
            # 'handlers': ['console', 'file'],
            'level': DEFAULT_LEVEL,
        },
        'ansible_galaxy_cli': {
            # 'handlers': ['console', 'file'],
            'level': DEFAULT_LEVEL,
        },
    }
}


def setup(logging_config=None):
    logging_config = logging_config or {}

    conf = logging.config.dictConfig(logging_config)

    log = logging.getLogger(__name__)

    #root_logger = logging.getLogger('')
    #root_handler = logging.StreamHandler()
    #formatter = color_debug.ColorFormatter()
    #root_handler.setFormatter(formatter)
    #root_logger.addHandler(root_handler)

    from akl import alogging
    log = alogging.default_setup('')
    # log.debug('foo')
    # import logging_tree
    # logging_tree.printout()
    return conf


def setup_default():
    return setup(logging_config=DEFAULT_LOGGING_CONFIG)
