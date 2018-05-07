import copy
import logging
import six

from ansible_galaxy import exceptions
from ansible_galaxy.utils.content_name import repo_url_to_content_name
from ansible_galaxy.utils.role_spec import role_spec_parse
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS

log = logging.getLogger(__name__)


def parse_content_spec(content_spec_text):
    '''Given a text/str object describing a galaxy content, parse it.

    And return a dict with keys: 'name', 'src', 'scm', 'version'
    '''
    name = None
    scm = None
    src = None
    version = None

    spec_sections = ('src', 'version', 'name')
    spec_values = {'name': name, 'src': src, 'scm': scm, 'version': version}

    # This ignores any extra ','
    parts = content_spec_text.split(',')
    for section in spec_sections:
        try:
            spec_values[section] = parts.pop()
        except IndexError:
            continue
        log.debug('spec_values: %s', spec_values)

    log.debug('spec_values: %s parts: %s', spec_values, parts)
    if parts:
        msg = "Invalid content line (%s). Proper format is 'content_name[,version[,name]]'. There were two many commas." \
            % content_spec_text
        raise exceptions.GalaxyClientError(msg)

    if spec_values['name'] is None:
        spec_values['name'] = repo_url_to_content_name(src)

    if spec_values['src'] and '+' in spec_values['src']:
        (spec_values['scm'], spec_values['src']) = spec_values['src'].split('+', 1)

    log.debug('parsed content_spec_text="%s" into: %s', content_spec_text, spec_values)
    return spec_values


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

        # FIXME: why are we stripping the input in multiple places, should do it
        #        before passing it in
        return parse_content_spec(content.strip())

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
        # "role" style object
        log.debug('content="%s" appears to be a role', content)

        name = content['role']
        if ',' in name:
            # "old role" style object
            # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
            # Maintained for backwards compat
            content = role_spec_parse(content['role'])
        else:
            del content['role']
            content['name'] = name
    else:
        # "content style" object
        log.debug('content="%s" does not appear to be an old style role', content)

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
