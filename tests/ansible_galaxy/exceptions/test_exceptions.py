import logging

from ansible_galaxy import exceptions
from ansible_galaxy.utils.text import to_text

log = logging.getLogger(__name__)


def test_galaxy_error():
    exc = exceptions.GalaxyError()
    log.debug('exc: %s', exc)


def test_galaxy_download_error_no_args():
    exc = exceptions.GalaxyDownloadError()
    log.debug('exc: %s', exc)


# Format: byte representation, text representation, encoding of byte representation
VALID_STRINGS = (
    (b'abcde', u'abcde', 'ascii'),
    (b'caf\xc3\xa9', u'caf\xe9', 'utf-8'),
    (b'caf\xe9', u'caf\xe9', 'latin-1'),
    # u'くらとみ'
    (b'\xe3\x81\x8f\xe3\x82\x89\xe3\x81\xa8\xe3\x81\xbf', u'\u304f\u3089\u3068\u307f', 'utf-8'),
    (b'\x82\xad\x82\xe7\x82\xc6\x82\xdd', u'\u304f\u3089\u3068\u307f', 'shift-jis'),
)


def _text_encoding():
    for valid_string, txtrpr, encoding in VALID_STRINGS:
        log.debug('valid_string: %s txtrpr: %s encoding: %s', valid_string, txtrpr, encoding)
        exc = exceptions.GalaxyDownloadError(to_text(valid_string))
        log.debug('exc: %s', exc)
        log.debug(exc)
        log.debug('exc(str): %s', str(exc))
        log.debug('exc(repr): %s', repr(exc))
        ttext = to_text(valid_string)
        log.debug('%s in %s: %s', ttext, '%s' % exc, ttext in '%s' % exc)
        assert ttext in '%s' % exc


def log_text(exc):
    log.debug('exc: %s', exc)
    log.debug(exc)
    log.debug('exc(str): %s', str(exc))
    log.debug('exc(repr): %s', repr(exc))


def _galaxy_download_error(msg, url):
    # url kw but no message
    exc = exceptions.GalaxyDownloadError(url=url)
    log.debug('exc: %s', exc)
    assert exc.url == url
    assert url in str(exc)

    # multiple args, but no url kwarg
    exc = exceptions.GalaxyDownloadError(url, msg)
    log.debug('exc: %s', exc)
    assert exc.url is None

    # a message arg and a url kwarg
    exc = exceptions.GalaxyDownloadError(msg, url=url)
    log.debug('exc: %s', exc)
    assert exc.url == url
    assert url in str(exc)
    assert msg in str(exc)

    # just a single message arg, no url
    exc = exceptions.GalaxyDownloadError(msg)
    log.debug('exc: %s', exc)
    assert exc.url is None
    assert msg in str(exc)


def test_galaxy_download_error():
    url = 'http://error.example.com'
    msgs = ['some_message', u'caf\xe9']

    for msg in msgs:
        _galaxy_download_error(msg, url)
