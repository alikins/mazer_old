#!/bin/bash -evux

# install strategy plugins from a plugin only  repo
#rm -rf ~/.ansible/content
#ansible-galaxy-cli install -t strategy_plugin alikins.content-just-strategy-plugins
#tree ~/.ansible/content
#[ -d ~/.ansible/content/strategy_plugins ]


# test 'init'
rm -rf ~/.ansible/test-roles
mkdir -p ~/.ansible/test-roles
ansible-galaxy-cli init --init-path ~/.ansible/test-roles some_role1
tree ~/.ansible/test-roles
ROLE_NAME="some_role1"
[ -d ~/.ansible/test-roles/ ]
[ -d ~/.ansible/test-roles/${ROLE_NAME} ]
[ -f ~/.ansible/test-roles/${ROLE_NAME}/README.md ]
[ -d ~/.ansible/test-roles/${ROLE_NAME}/meta ]
[ -f ~/.ansible/test-roles/${ROLE_NAME}/meta/main.yml ]
[ -d ~/.ansible/test-roles/${ROLE_NAME}/files ]
[ -d ~/.ansible/test-roles/${ROLE_NAME}/tasks ]
[ -f ~/.ansible/test-roles/${ROLE_NAME}/tasks/main.yml ]
[ -d ~/.ansible/test-roles/${ROLE_NAME}/vars ]


# install a single role from a multi-content archive from galaxy
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t role testing.ansible-testing-content.test-role-c
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]
[ -d "${HOME}/.ansible/content/roles/test-role-c" ]
[ -d "${HOME}/.ansible/content/roles/test-role-c/meta" ]
[ -f "${HOME}/.ansible/content/roles/test-role-c/meta/main.yml" ]
[ -d "${HOME}/.ansible/content/roles/test-role-c/vars" ]
[ -f "${HOME}/.ansible/content/roles/test-role-c/vars/main.yml" ]
[ ! -d "${HOME}/.ansible/content/roles/alikins.testing-content" ]

# ansible-galaxy-cli list -p ~/.ansible/test-roles

# ansible-galaxy-cli search  --author=alikins

# ansible-galaxy-cli search  strategy

# install 'all' from a multi-content repo
rm -rf ~/.ansible/content
ansible-galaxy-cli install alikins.ansible-testing-content
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]
[ -d "${HOME}/.ansible/content/roles/test-role-b" ]
[ -d ~/.ansible/content/library ]
[ -d ~/.ansible/content/strategy_plugins ]
[ -d ~/.ansible/content/filter_plugins ]
[ -d ~/.ansible/content/module_utils ]
# not yet
# [ -f ~/.ansible/content/library/.galaxy_install_info ]

# install role
rm -rf ~/.ansible/content
ansible-galaxy-cli install alikins.ansible-role-awx
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]
[ -d ~/.ansible/content/roles/alikins.ansible-role-awx ]
[ -d ~/.ansible/content/roles/alikins.ansible-role-awx/meta ]
[ -f ~/.ansible/content/roles/alikins.ansible-role-awx/meta/main.yml ]
[ -d ~/.ansible/content/roles/alikins.ansible-role-awx/tasks ]
[ -f ~/.ansible/content/roles/alikins.ansible-role-awx/tasks/main.yml ]
[ -d ~/.ansible/content/roles/alikins.ansible-role-awx/vars ]
[ -f ~/.ansible/content/roles/alikins.ansible-role-awx/vars/RedHat.yml ]



# install modules from a multi-content repo
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t module alikins.ansible-testing-content
tree ~/.ansible/content
[ -d ~/.ansible/content/library ]
# not all the modules, but at least more than one
for module_file in elasticsearch_plugin.py kibana_plugin.py redis.py ;
do
    echo
    # [ -f "${HOME}/.ansible/content/library/${module_file}" ]
done

# install 'all' from a repo with plugins and modules but not roles or meta repo
rm -rf ~/.ansible/content
ansible-galaxy-cli install alikins.ansible-content-no-meta
tree ~/.ansible/content
[ -d ~/.ansible/content/library ]
[ -d ~/.ansible/content/callback_plugins ]
[ -d ~/.ansible/content/action_plugins ]
# not yet
# [ -f ~/.ansible/content/library/.galaxy_install_info ]


# install strategy plugins from a multi-content repo
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t strategy_plugin alikins.ansible-testing-content
tree ~/.ansible/content
[ -d ~/.ansible/content/strategy_plugins ]
for strat_file in debug.py free.py linear.py ;
do
    [ -f "${HOME}/.ansible/content/strategy_plugins/${strat_file}" ]
done


# install a single module
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t module testing.ansible-testing-content.elasticsearch_plugin
tree ~/.ansible/content
[ -d ~/.ansible/content/library/ ]
[ -f ~/.ansible/content/library/elasticsearch_plugin.py ]

# FIXME
# [ ! -e ~/.ansible/content/library/kibana_plugin.py ]






# install a signle module
# ansible-galaxy-cli install -t module atestuseraccount.testing-content.elasticsearch_plugin.py
# tree ~/.ansible/content
# [ -d ~/.ansible/content/library/alikins.testing-content ]



# install modules from a scm url
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git
tree ~/.ansible/content

# install all from a scm url
rm -rf ~/.ansible/content
ansible-galaxy-cli install  git+https://github.com/atestuseraccount/ansible-testing-content.git
tree ~/.ansible/content

# install from a scm url again without cleaning up (should fail)
ansible-galaxy-cli install  git+https://github.com/atestuseraccount/ansible-testing-content.git && :
RC=$?
echo "rc was $RC (70 is expected)"
[ $RC -eq 70 ]

# install from a scm url again but with --force without cleaning up (should work)
ansible-galaxy-cli install --force git+https://github.com/atestuseraccount/ansible-testing-content.git
tree ~/.ansible/content

# install all with a version from scm
rm -rf ~/.ansible/content
ansible-galaxy-cli install git+https://github.com/atestuseraccount/ansible-testing-content.git,0.0.1
tree ~/.ansible/content

# install all with a version from scm
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git,0.0.1
tree ~/.ansible/content

# install roles from a multi content archive from a scm url
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t role  git+https://github.com/atestuseraccount/ansible-testing-content.git
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]
[ -d "${HOME}/.ansible/content/roles/test-role-b" ]
[ -d "${HOME}/.ansible/content/roles/test-role-b/meta" ]
[ -f "${HOME}/.ansible/content/roles/test-role-b/meta/main.yml" ]
[ -d "${HOME}/.ansible/content/roles/test-role-b/vars" ]
[ -f "${HOME}/.ansible/content/roles/test-role-b/vars/main.yml" ]
[ ! -d "${HOME}/.ansible/content/roles/alikins.testing-content" ]


# install roles from a multi-content archive from galaxy
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t role testing.ansible-testing-content
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]
[ -d "${HOME}/.ansible/content/roles/test-role-b" ]
[ -d "${HOME}/.ansible/content/roles/test-role-b/meta" ]
[ -f "${HOME}/.ansible/content/roles/test-role-b/meta/main.yml" ]
[ -d "${HOME}/.ansible/content/roles/test-role-b/vars" ]
[ -f "${HOME}/.ansible/content/roles/test-role-b/vars/main.yml" ]
[ ! -d "${HOME}/.ansible/content/roles/alikins.testing-content" ]

# install an apb archive from galaxy
rm -rf ~/.ansible/content
ansible-galaxy-cli install alikins.mssql-apb
tree ~/.ansible/content
[ -d ~/.ansible/content/apbs ]
# should dir be mssql or mssql-apb? apb.yml name: is mssql-apb
[ -d ~/.ansible/content/apbs/mssql-apb ]

# install just roles from an apb archive from galaxy
rm -rf ~/.ansible/content
ansible-galaxy-cli install -t role alikins.mssql-apb
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]
[ -d ~/.ansible/content/roles/deprovision-mssql-apb ]

# install to a diff dir via --content-path from scm
CONTENT_DIR=$(mktemp -d)
ansible-galaxy-cli install --content-path "${CONTENT_DIR}" git+https://github.com/atestuseraccount/ansible-testing-content.git
tree "${CONTENT_DIR}"
rm -rf "${CONTENT_DIR}"

# not testing ansible-galaxy-cli.yml support yet
exit 0

# install from a repo with a ansible-galaxy-cli.yml
rm -rf ~/.ansible/content
ansible-galaxy-cli install alikins.test-galaxy-content-galaxyfile
tree ~/.ansible/content
[ -d ~/.ansible/content/library ]
[ -f ~/.ansible/content/library/module_c.py ]
[ -f ~/.ansible/content/library/galaxyfile_sample_module.py ]
[ -f ~/.ansible/content/library/galaxyfile_playbook_sample_module.py ]
[ ! -e ~/.ansible/content/README.md ]

# not yet
# [ -f ~/.ansible/content/library/.galaxy_install_info ]


# TODO: start converting to a test script
ls -lart ~/.ansible/content/roles/alikins.testing-content
# grep role_name ~/.ansible/content/roles/alikins.testing-content/meta/main.yml
# ~/.ansible/content/roles/.galaxy_install_info

# install 'all' from a multi-content repo
rm -rf ~/.ansible/content
ansible-galaxy-cli install alikins.ansible-testing-content
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]


# install all modules
ansible-galaxy-cli install -t module testing.ansible-testing-content
tree ~/.ansible/content
[ -d ~/.ansible/content/roles ]

exit 0

# insall a signle module from a scm url
ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git,name=elasticsearch_plugin.py

# install a specific version of all
ansible-galaxy-cli install -t module atestuseraccount.galaxy-test-role,0.0.1
ansible-galaxy-cli install -t module atestuseraccount.galaxy-test-role,version=0.0.1

# The following commands use the SCM+URL convention to install version 0.0.1 of all modules:

ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git,0.0.1
ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git,version=0.0.1

# install specific version of signal
ansible-galaxy-cli install -t module atestuseraccount.galaxy-test-role,0.0.1
ansible-galaxy-cli install -t module atestuseraccount.galaxy-test-role,version=0.0.1

# The following commands use the SCM+URL convention to install version 0.0.1 of all modules:

ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git,0.0.1
ansible-galaxy-cli install -t module git+https://github.com/atestuseraccount/ansible-testing-content.git,version=0.0.1


# traditional roles https://github.com/ansible/galaxy-cli/wiki/Traditional-Roles

# The following uses the Galaxy name to install the latest version of the role:

ansible-galaxy-cli install alikins.ansible-role-awx

# Here we use the SCM+URL convention to install the latest version:
ansible-galaxy-cli install git+https://github.com/geerlingguy/ansible-role-awx.git

# Install a specific version
# Using the Galaxy name

# Using the Galaxy name, the version can be passed using the following two methods:

ansible-galaxy-cli install alikins.ansible-role-awx,1.0.0
ansible-galaxy-cli install alikins.awx,version=1.0.0

#Using the SCM+URL convention, the version can be passed using the following two methods:
ansible-galaxy-cli install git+https://github.com/geerlingguy/ansible-role-awx.git,1.0.0
ansible-galaxy-cli install git+https://github.com/geerlingguy/ansible-role-awx.git,version=1.0.0


# Traditional roles From a Multicontent Repository
# In this scenario, the repository contains multiple content types, including several roles. Examples are based on atestuseraccount/ansible-testing-content.

# Assumptions
# ANSIBLE_ROLES_PATH is not set in the environment
# ANSIBLE_GALAXY_CONTENT_PATH is not set in the environment
# Neither roles_path nor galaxy_content_path is set in ansible.cfg
# Based on the above settings, roles will be installed to the default content path of ~/.ansible/content.
# Before each command is executed, the roles subdirectory within the content path is empty.
# A version is an SCM tag on the repository
# Modules are found in the root level library directory of the source repository
# The repository does not contain an ansible-galaxy-cli.yml metadata file

# install the latest version of all roles
# The following uses the Galaxy name to install the latest version of all roles:
# Expected Result
# All roles from the repository are installed.

# The name of the subdirectory containing each installed role matches the Galaxy server naming convention of namespace.role_name.

# The path to each installed role is ~/.ansible/content/roles/atestuseraccount.<role_name>.

# The role ansible-test-role-1 has a role_name value of testing-role set in meta/main.yml, and will be installed to the directory ~/.ansible/content/roles/atestuseraccount.testing-role

# Following the default role naming conventions, the role ansible-role-foobar will be installed to the directory ~/.ansible/content/roles/atestuseraccount.foobar

# The ~/.ansible/content/roles/.galaxy_install_info contains an entry for each role, and for each, the version reflects the latest version found in the repository, which at the time of this writing is 1.1.0.


ansible-galaxy-cli install -t role alikins.testing-content
RC=$?

# TODO: start converting to a test script
ls -lart ~/.ansible/content/roles/alikins.testing-content
grep role_name ~/.ansible/content/roles/alikins.testing-content/meta/main.yml
~/.ansible/content/roles/.galaxy_install_info

# Here we use the SCM+URL convention to install the latest version of all roles:
ansible-galaxy-cli install -t role git+https://atestuseraccount/ansible-testing-content.git


# install the latest version of a single role

# The following uses the Galaxy name to install the latest version of a single role:
ansible-galaxy-cli install -t role atestuseraccount.ansible-testing-content.testing-role

# Here we use the SCM+URL convention to install the latest version of a single role:
ansible-galaxy-cli install -t role git+https://atestuseraccount/ansible-testing-content.git,name=ansible-test-role-1

# install a specific version of all roles

# Using the Galaxy name, the version can be passed using the following two methods:
ansible-galaxy-cli install -t role atestuseraccount.ansible-testing-content,0.0.1
ansible-galaxy-cli install -t role atestuseraccount.ansible-testing-content,version=0.0.1

#Using the SCM+URL convention, the version can be passed using the following two methods:
ansible-galaxy-cli install -t role git+https://github.com/atestuseraccount/ansible-testing-content.git,0.0.1
ansible-galaxy-cli install -t role git+https://github.com/atestuseraccount/ansible-testing-content,version=0.0.1

# install specific version of a single role

# The following commands uses the Galaxy name to install a specific version of a single role:
ansible-galaxy-cli install -t role atestuseraccount.ansible-testing-content.testing-role,0.0.1
ansible-galaxy-cli install -t role atestuseraccount.ansible-testing-content.testing-role,version=0.0.1

# Here we use the SCM+URL convention to install the latest version of a single role:
ansible-galaxy-cli install -t role git+https://atestuseraccount/ansible-testing-content.git,name=ansible-test-role-1,version=0.0.1

