"""Exceptions used by ansible_galaxy client library"""


class GalaxyError(Exception):
    """Base exception for ansible_galaxy library and ansible_galaxy_cli app"""
    pass


class GalaxyClientError(GalaxyError):
    """Base exception for ansible_galaxy library

    Exceptions that escape from ansible_galaxy. should be based on this class"""
    pass


class ParserError(GalaxyError):
    """Base exception raised for errors while parsing galaxy content"""
    pass


# TODO: attrs for http code, url, msg or just reuse http exception from elsewhere
class GalaxyDownloadError(GalaxyError):
    '''Raise when there is an error downloading galaxy content'''
    pass


class GalaxyClientAPIConnectionError(GalaxyClientError):
    '''Raised if there were errors connecting to the Galaxy REST API'''
    pass


# TODO: proper rst docstrings with api info
class GalaxyConfigFileError(GalaxyClientError):
    '''Raised where there is an error loading or parsing a config file

       has a 'config_file_path' attribute with the config file path'''

    def __init__(self, *args, **kwargs):
        config_file_path = kwargs.pop('config_file_path', None)
        super(GalaxyConfigFileError, self).__init__(*args, **kwargs)
        self.config_file_path = config_file_path
