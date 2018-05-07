import logging

from ansible_galaxy.utils import yaml_parse

log = logging.getLogger(__name__)


def parse_spec(content_spec):
    result = yaml_parse.yaml_parse(content_spec)
    log.debug('result=%s', result)
    return result


def assert_keys(content_spec, name=None, version=None, scm=None, src=None):
    name = name or ''
    src = src or ''
    assert isinstance(content_spec, dict)

    # TODO: should it default to empty string?
    assert content_spec['name'] == name, \
        'content_spec name=%s does not match expected name=%s' % (content_spec['name'], name)
    assert content_spec['version'] == version
    assert content_spec['scm'] == scm
    assert content_spec['src'] == src, \
        'content_spec src=%s does not match expected src=%s' % (content_spec['src'], src)


def test_yaml_parse_empty_string():
    spec = ''
    result = parse_spec(spec)

    assert_keys(result, name='', version=None, scm=None, src='')


def test_yaml_parse_just_name():
    spec = 'some_content'
    result = parse_spec(spec)

    assert_keys(result, name='some_content', version=None, scm=None, src='some_content')


def test_yaml_parse_name_and_version():
    spec = 'some_content,1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='some_content', version='1.0.0', scm=None, src='some_content')


def test_yaml_parse_name_and_version_key_value():
    spec = 'some_content,version=1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='some_content', version='1.0.0', scm=None, src='some_content')


def test_yaml_parse_name_github_url():
    buf = 'git+https://github.com/geerlingguy/ansible-role-awx.git,1.0.0'
    result = parse_spec(buf)

    assert_keys(result, name='awx', version='1.0.0', scm='git', src='https://github.com/geerlingguy/ansible-role-awx.git')


# See https://github.com/ansible/galaxy-cli/wiki/Content-Versioning#versions-in-galaxy-cli
#
# "When providing a version, provide the semantic version with or without the leading 'v' or 'V'."
#
def test_yaml_parse_name_and_version_leading_V():
    spec = 'some_content,V1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='some_content', version='1.0.0', scm=None, src='some_content')


# proving a name and a version as comma separated key values
def test_yaml_parse_name_with_name_key_value():
    spec = 'some_content,name=other_name'
    result = parse_spec(spec)

    # TODO: what should 'src' be for this cases?
    assert_keys(result, name='other_name', version=None, scm=None, src='some_content')


def test_yaml_parse_a_list_of_strings():
    spec = ['some_content', 'something_else']
    parse_spec(spec)

    # TODO: verify we get the right exception


def test_yaml_parse_an_empty_dict():
    spec = {}
    result = parse_spec(spec)

    assert_keys(result, name=None, version=None, scm=None, src=None)


def test_yaml_parse_a_dict():
    spec = {'name': 'some_name',
            'version': '1.2.4',
            'src': 'galaxy.role'}
    result = parse_spec(spec)

    assert_keys(result, name='some_name', version='1.2.4', scm=None, src='galaxy.role')


# comments in yaml_parse.py indicate src='galaxy.role,version,name' is supposed to work
def test_yaml_parse_a_dict_with_conflicts():
    spec = {'name': 'some_name1',
            'version': '1.2.3',
            'src': 'galaxy.role,1.0.0,some_name2'}
    result = parse_spec(spec)

    assert_keys(result, name='some_name2', version='1.0.0', scm=None, src=None)
