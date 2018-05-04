import six

from ansible_galaxy import exceptions
from ansible_galaxy.utils.content_name import repo_url_to_content_name
from ansible_galaxy.utils.role_spec import role_spec_parse
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS


# FIXME: not really yaml,
# FIXME: whats the diff between this and role_spec_parse?
# TODO: return a new GalaxyContentMeta
# TODO: dont munge the passed in content
# TODO: split into smaller methods
# FIXME: does this actually use yaml?
# FIXME: kind of seems like this does two different things
def yaml_parse(content):
    """parses the passed in yaml string and returns a dict with name/src/scm/version

    Or... if the passed in 'content' is a dict, it either creates role or if not a role,
    it copies the dict and sets name/src/scm/version in it"""

    # TODO: move to own method
    if isinstance(content, six.string_types):
        name = None
        scm = None
        src = None
        version = None
        if ',' in content:
            if content.count(',') == 1:
                (src, version) = content.strip().split(',', 1)
            elif content.count(',') == 2:
                (src, version, name) = content.strip().split(',', 2)
            else:
                raise exceptions.GalaxyClientError("Invalid content line (%s). Proper format is 'content_name[,version[,name]]'" % content)
        else:
            src = content

        if name is None:
            name = repo_url_to_content_name(src)
        if '+' in src:
            (scm, src) = src.split('+', 1)

        return dict(name=name, src=src, scm=scm, version=version)

    # Not sure what will/should happen if content is not a Mapping or a string
    if 'role' in content:
        name = content['role']
        if ',' in name:
            # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
            # Maintained for backwards compat
            content = role_spec_parse(content['role'])
        else:
            del content['role']
            content['name'] = name
    else:
        content = content.copy()

        if 'src'in content:
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
            content.pop(key)

    return content
