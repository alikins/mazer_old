#!/usr/bin/python
# main 'entrypoint' for ansible-galaxy-cli
# NOTE: not an actual setuptools 'entrypoint' yet

import sys

from ansible_galaxy_cli.main import main

if __name__ == '__main__':
    sys.exit(main())
