# galaxy-cli

ansible-galaxy is a tool to manage ansible related content from https://galaxy.ansible.com

## Features

- More than just roles!
- multi content repos
  - repos that can contain multiple roles as well
    as multiple content types (modules, plugins, etc)

```
$ ansible-galaxy install alikins.testing-content
- extracting all content in alikins.testing-content to content directories
- alikins.testing-content all was installed successfully to /home/adrian/.ansible/content
$ tree ~/.ansible/content
/home/adrian/.ansible/content/
├── action_plugins
│   └── add_host.py
├── filter_plugins
│   ├── json_query.py
├── library
│   ├── elasticsearch_plugin.py
│   ├── kibana_plugin.py
├── lookup_plugins
│   └── openshift.py
├── module_utils
│   ├── inventory.py
│   ├── raw.py
│   └── scale.py
├── roles
│   ├── test-role-a
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   └── main.yml
│   │   ├── tests
│   │   │   ├── inventory
│   │   │   └── test.yml
│   │   └── vars
│   │       └── main.yml
│   ├── test-role-b
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── README.md
│   │   ├── tasks
│   │   │   └── main.yml
│   │   ├── tests
│   │   │   ├── inventory
│   │   │   └── test.yml
│   │   └── vars
│   │       └── main.yml
└── strategy_plugins
    ├── debug.py
    └── linear.py
```
- support for repos of modules, plugins, etc

        demo:

    (demo installing regular role  (geerlinguy guy stuff))

- support for installing content type specific subsets of repos

ie, install all of the modules and just the modules from a repo that also
has roles, plugins, etc

``` shell
# install just the strategy plugins from alikins.testing-content

rm -rf ~/.ansible/content && ansible-galaxy install -t strategy_plugin alikins.testing-content
tree ~/.ansible/content

# install just the modules

rm -rf ~/.ansible/content && ansible-galaxy install -t module alikins.testing-content
```
  - support installing content type specific subsets of roles

## Install

### From source

```
$ git clone https://github.com/ansible/galaxy-cli.git
$ cd galaxy-cli
$ python setup.py install
```

Or install the requirements via pip:

```
$ pip install -r requirements.txt
```

### Via pip (from git)
```
pip install -v git+ssh://git@github.com/ansible/galaxy-cli.git
```

## Testing

### unit testing

galaxy-cli uses pytest for unit tests.

#### test requirements

To install test requirements, use pip to install the requirements in requirements_test.txt:

```
pip install -r requirements_test.txt
To run unit tests

via `tox` for default platforms (python 2.6, 2.7, 3.6):

```
$ tox
```

via 'pytest' directly

```
$ pytest tests/
```
