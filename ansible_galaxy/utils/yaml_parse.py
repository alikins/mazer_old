import copy
import logging
import six

from ansible_galaxy import exceptions
from ansible_galaxy.utils.content_name import repo_url_to_content_name
from ansible_galaxy.utils.role_spec import role_spec_parse
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS

log = logging.getLogger(__name__)


def split_kwarg(spec_string, valid_keywords):
    if '=' not in spec_string:
        return (None, spec_string)

    parts = spec_string.split('=', 1)

    if parts[0] in valid_keywords:
        return (parts[0], parts[1])
    return (None, spec_string)


def split_comma(spec_string, valid_keywords):
    # res = []
    comma_parts = spec_string.split(',')
    for comma_part in comma_parts:
        kw_parts = split_kwarg(comma_part, valid_keywords)
        log.debug('kw_parts: %s', kw_parts)
        yield kw_parts


def split_content_spec(spec_string, valid_keywords):
    comma_splitter = split_comma(spec_string, valid_keywords)

    info = {}
    for kw in valid_keywords:
        print('kw: %s' % kw)
        try:
            key, value = comma_splitter.next()
        except StopIteration:
            return info

        print('key=%s value=%s' % (key, value))
        if key:
            info[key] = value
        else:
            info[kw] = value

    return info


def parse_content_spec(content_spec_text):
    '''Given a text/str object describing a galaxy content, parse it.

    And return a dict with keys: 'name', 'src', 'scm', 'version'
    '''
    name = None
    scm = None
    src = None
    version = None

    # TODO: tokenizer?
    #if ',' in content_spec_text:
    #    if content_spec_text.count(',') == 1:
    #        (src, version) = content_spec_text.strip().split(',', 1)
    #    elif content_spec_text.count(',') == 2:
    #        (src, version, name) = content_spec_text.strip().split(',', 2)
    #    else:
    #        raise exceptions.GalaxyClientError("Invalid content line (%s). Proper format is 'content_name[,version[,name]]'" % content_spec_text)
    # else:
    #    src = content_spec_text

    valid_keywords = ('src', 'version', 'name', 'scm')
    data = {'src': None,
            'name': None,
            'version': None,
            'scm': None}
    split_data = split_content_spec(content_spec_text, valid_keywords)
    print('split_data: %s' % split_data)

    data.update(split_data)
    print('data: %s' % data)

    if data['name'] is None:
        scm_name = repo_url_to_content_name(data['src'])
        data['name'] = scm_name
        if '+' in data['src']:
            (scm_url, scm_src) = data['src'].split('+', 1)
            data['scm'] = scm_url
            data['src'] = scm_src
        print('predata: %s' % data)

    # data = dict(name=name, src=src, scm=scm, version=version)

    # log.debug('parsed content_spec_text="%s" into: %s', content_spec_text, data)
    return data


# FIXME: not really yaml,
# FIXME: whats the diff between this and role_spec_parse?
# TODO: return a new GalaxyContentMeta
# TODO: dont munge the passed in content
# TODO: split into smaller methods
# FIXME: does this actually use yaml?
# FIXME: kind of seems like this does two different things
# FIXME: letting this take a string _or_ a mapping seems troubleprone
def yaml_parse(content):
    """parses the passed in yaml string and returns a dict with name/src/scm/version

    Or... if the passed in 'content' is a dict, it either creates role or if not a role,
    it copies the dict and sets name/src/scm/version in it"""

    # FIXME: rm once we stop clobbering the passed in content, we can stop making a
    #        copy of orig_content as this is just for logging
    #        the original value

    if isinstance(content, six.string_types):
        log.debug('parsing content="%s" as a string', content)
        orig_content = copy.deepcopy(content)
        res = parse_content_spec(content)
        log.debug('parsed spec="%s" -> %s', content, res)
        return res

    log.debug('content="%s" is not a string (it is a %s) so we are assuming it is a dict',
              content, type(content))

    orig_content = copy.deepcopy(content)

    # Not sure what will/should happen if content is not a Mapping or a string
    # FIXME: if content is not a string or a dict/map, throw a reasonable error.
    #        for ex, if a list of strings is passed in, the content.copy() below throws
    #        an attribute error
    # FIXME: This isn't a 'parse' at all, if we want to convert a dict/map to the specific
    #        type of dict we expect, should be a different method
    # FIXME: what is expected to happen if passed an empty dict?
    if 'role' in content:
        log.debug('content="%s" appears to be a role', content)

        name = content['role']
        if ',' in name:
            # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
            # Maintained for backwards compat
            content = role_spec_parse(content['role'])
        else:
            del content['role']
            content['name'] = name
    else:
        log.debug('content="%s" does not appear to be a role', content)

        # FIXME: just use a new name already
        # FIXME: this fails for objects with no dict attribute, like a list
        content = content.copy()

        if 'src' in content:
            # New style: { src: 'galaxy.role,version,name', other_vars: "here" }
            if 'github.com' in content["src"] and 'http' in content["src"] and '+' not in content["src"] and not content["src"].endswith('.tar.gz'):
                content["src"] = "git+" + content["src"]

            if '+' in content["src"]:
                (scm, src) = content["src"].split('+')
                content["scm"] = scm
                content["src"] = src

            if 'name' not in content:
                content["name"] = repo_url_to_content_name(content["src"])

        if 'version' not in content:
            content['version'] = ''

        if 'scm' not in content:
            content['scm'] = None

    for key in list(content.keys()):
        if key not in VALID_ROLE_SPEC_KEYS:
            log.debug('removing invalid key: %s', key)

            content.pop(key)

    log.debug('"parsed" content="%s" into: %s', orig_content, content)

    return content
