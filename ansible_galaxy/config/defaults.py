
# a list of tuples that is fed to an OrderedDict
DEFAULTS = [
    # defaults ?
    ('defaults', {}),

    #
    ('servers',  [
        {'url': 'https://galaxy-qa.ansible.com',
         'validate_certs': True,
         'token': None,
         },
    ]),

    # In order of priority
    ('content_roots', [
        '~/.ansible/content',
        '/usr/share/ansible/content',
    ]),

    # runtime options
    ('options', {
        'role_skeleton_path': None,
        'role_skeleton_ignore': ["^.git$", "^.*/.git_keep$"],
    }),
    ('version', 1),
]

# FIXME: replace with logging config
VERBOSITY = 0
CONFIG_FILE = '~/.ansible/galaxy.yml'
