import logging

import pytest

from ansible_galaxy import exceptions
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS
from ansible_galaxy.utils import yaml_parse


log = logging.getLogger(__name__)


# TODO/FIXME: use pytest param fixtures


def parse_spec(content_spec):
    result = yaml_parse.yaml_parse(content_spec)
    log.debug('result=%s', result)
    return result


def assert_keys(content_spec, name=None, version=None, scm=None, src=None):
    # name = name or ''
    # src = src or ''
    assert isinstance(content_spec, dict)

    # TODO: should it default to empty string?
    assert content_spec['name'] == name, \
        'content_spec name=%s does not match expected name=%s' % (content_spec['name'], name)
    assert content_spec['version'] == version
    assert content_spec['scm'] == scm
    assert content_spec['src'] == src, \
        'content_spec src=%s does not match expected src=%s' % (content_spec['src'], src)


just_src = {'src': 'something'}
src_ver = {'src': 'something',
           'version': '1.2.3'}
src_name = {'src': 'something',
            'name': 'somename'}
full_info = {'src': 'something',
             'version': '1.2.3',
             'name': 'somename'}
kwarg_test_cases = \
    [('something', just_src),
     ('something,1.2.3', src_ver),
     ('something,version=1.2.3', src_ver),
     ('something,1.2.3,somename', full_info),
     ('something,1.2.3,name=somename', full_info),
     ('something,name=somename,version=1.2.3', full_info),
     ('something,1.2.3,somename', full_info),
     # dont want to expect this to work
     ('something,name=somename,1.2.3', full_info)]


@pytest.fixture(scope='module',
                params=kwarg_test_cases,
                ids=[x[0] for x in kwarg_test_cases])
def split_kwarg(request):
    yield request.param


def test_split_kwarg(split_kwarg):
    valid_keywords = ('name', 'version')
    result = yaml_parse.split_kwarg(split_kwarg[0], valid_keywords)
    log.debug('spec=%s result=%s', split_kwarg[0], [x for x in result])


def test_split_comma(split_kwarg):
    valid_keywords = ('name', 'version')
    result = yaml_parse.split_comma(split_kwarg[0], valid_keywords)
    log.debug('spec=%s result=%s', split_kwarg[0], [x for x in result])


def test_split_content_spec(split_kwarg):
    valid_keywords = ('src', 'version', 'name', 'scm')
    result = yaml_parse.split_content_spec(split_kwarg[0], valid_keywords)
    log.debug('spec=%s result=%s', split_kwarg[0], result)
    assert result == split_kwarg[1]


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
    spec = 'git+https://github.com/geerlingguy/ansible-role-awx.git,1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='awx', version='1.0.0', scm='git', src='https://github.com/geerlingguy/ansible-role-awx.git')


def test_yaml_parse_name_github_url_keyword_version():
    spec = 'git+https://github.com/geerlingguy/ansible-role-awx.git,version=1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='awx', version='1.0.0', scm='git', src='https://github.com/geerlingguy/ansible-role-awx.git')


def test_yaml_parse_name_non_github_url():
    buf = 'git+https://git.example.com/geerlingguy/ansible-role-awx.git,1.0.0'
    result = parse_spec(buf)

    assert_keys(result, name='awx', version='1.0.0', scm='git', src='https://git.example.com/geerlingguy/ansible-role-awx.git')


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


def test_yaml_parse_a_dict_with_extra_invalid_keys():
    spec = {'name': 'some_name',
            'version': '1.2.4',
            'src': 'galaxy.role',
            'favorite_tea': 'sweet',
            'module': 'some_module',
            'url': 'http://example.com/galaxy/foo'}
    result = parse_spec(spec)

    assert_keys(result, name='some_name', version='1.2.4', scm=None, src='galaxy.role')
    result_keys = set(result.keys())
    valid_keys = set(VALID_ROLE_SPEC_KEYS)
    extra_keys = result_keys.difference(valid_keys)
    assert not extra_keys, \
        'Found extra invalid keys in the result. extra_keys=%s, result=%s, valid_keys=%s' % \
        (extra_keys, result, valid_keys)

    assert_keys(result, name='some_name', version='1.2.4', scm=None, src='galaxy.role')


# comments in yaml_parse.py indicate src='galaxy.role,version,name' is supposed to work
def test_yaml_parse_a_dict_with_conflicts():
    spec = {'name': 'some_name1',
            'version': '1.2.3',
            'src': 'galaxy.role,1.0.0,some_name2'}
    result = parse_spec(spec)

    assert_keys(result, name='some_name1', version='1.0.0', scm=None, src=None)


def test_yaml_parse_a_old_style_role_dict():
    spec = {'role': 'some_role',
            'version': '1.2.4',
            'src': 'galaxy.role'}
    result = parse_spec(spec)

    # FIXME: requiring a different set of asserts to test the results for the role
    #        case points to this method doing too many things, being passed too many different things,
    #        and returning too many different things
    name = 'some_role'
    src = 'galaxy.role'
    assert isinstance(result, dict)
    assert result['name'] == name, \
        'content_spec name=%s does not match expected name=%s' % (result['name'], name)
    assert result['version'] == '1.2.4'
    assert result['src'] == src, \
        'content_spec src=%s does not match expected src=%s' % (result['src'], src)


# FIXME: I'm not real sure what the result of this is supposed to be
def test_yaml_parse_a_comma_sep_style_role_dict_with_version():
    src = 'galaxy.role,1.2.4'
    spec = {'src': src}
    result = parse_spec(spec)

    # FIXME: wtf is 'src' expected to look like here?
    assert_keys(result, name=None, version='1.2.4', scm=None, src='galaxy.role')


# FIXME: I'm not real sure what the result of this is supposed to be
def test_yaml_parse_a_comma_sep_style_role_dict_with_name_version():
    src = 'galaxy.role,1.2.4,some_role'
    spec = {'src': src}
    result = parse_spec(spec)

    # FIXME: wtf is 'src' expected to look like here?
    assert_keys(result, name='galaxy.role', version='1.2.4', scm=None, src=src)


def parse_content_spec(content_spec):
    result = yaml_parse.parse_content_spec(content_spec)
    log.debug('result=%s', result)
    return result


def assert_just_keys(parse_result):
    valid_keys = ('name', 'src', 'scm', 'version')

    for key in valid_keys:
        assert key in parse_result, 'expected the results dict to have a "%s" key but it did not' % key

    for result_key in parse_result.keys():
        assert result_key in valid_keys, 'the results had unexpected key="%s"' % result_key


def test_parse_content_spec_src():
    spec_text = 'some_content'
    result = parse_content_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, name='some_content', version=None, scm=None, src='some_content')


def test_parse_content_spec_src_version():
    spec_text = 'some_content,1.0.0'
    result = parse_content_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, name='some_content', version='1.0.0', scm=None, src='some_content')


def test_parse_content_spec_src_version_name():
    spec_text = 'some_content,1.2.3,somename'
    result = parse_content_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, name='somename', version='1.2.3', scm=None, src='some_content')


def test_parse_content_spec_src_version_name_something_invalid():
    spec_text = 'some_content,1.2.3,somename,some_scm,some_garbage'
    result = parse_content_spec(spec_text)

    assert_keys(result, name='somename', version='1.2.3', scm='some_scm', src='some_content')


def test_parse_content_spec_src_key_value():
    spec_text = 'src=some_content'
    result = parse_content_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, name='some_content', version=None, scm=None, src='some_content')


def test_parse_content_spec_src_version_key_value():
    spec_text = 'some_content,version=1.0.0'
    result = parse_content_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, name='some_content', version='1.0.0', scm=None, src='some_content')


def test_parse_content_spec_src_version_name_key_value():
    spec_text = 'some_content,1.2.3,name=somename'
    result = parse_content_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, name='somename', version='1.2.3', scm=None, src='some_content')


def test_parse_content_spec_src_version_name_something_invalid_key_value():
    spec_text = 'some_content,1.0.0,name=some_name,foo=bar,some_garbage'
    try:
        parse_content_spec(spec_text)
    except exceptions.GalaxyClientError:
        return

    assert False, 'spec_text="%s" should have caused a GalaxyClientError' % spec_text
