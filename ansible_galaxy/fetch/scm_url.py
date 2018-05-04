import logging

# mv details of this here
from ansible_galaxy.utils import scm_archive

log = logging.getLogger(__name__)


class ScmUrlFetch(object):
    def __init__(self, scm_url, scm_spec):
        self.scm_url = scm_url
        self.scm_spec = scm_spec
        self.local_path = None

    def fetch(self):
        content_archive_path = scm_archive.scm_archive_content(**self.scm_spec)
        return content_archive_path
