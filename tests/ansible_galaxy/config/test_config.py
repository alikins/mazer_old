import logging

from ansible_galaxy.config import config

log = logging.getLogger(__name__)

CONFIG_SECTIONS = ['defaults', 'servers', 'content_roots', 'options']


def assert_object(config_obj):
    assert isinstance(config_obj, config.Config)

    for attr in CONFIG_SECTIONS:
        assert hasattr(config_obj, attr), 'Config instance does not have attr "%s"' % attr


def test_config_init():
    _config = config.Config()

    assert_object(_config)


def test_config_unknown_attr():
    _config = config.Config()

    assert hasattr(_config, 'not_a_valid_attr') is False
    try:
        blip = _config.not_a_valid_attr
    except AttributeError as e:
        log.debug(e, exc_info=True)
        return

    assert False, 'Expected to get an AttributeError accessing an unknown attr but did not and %s was returned' % blip


def test_config_from_empty_dict():
    config_data = {}
    _config = config.Config.from_dict(config_data)
    assert_object(_config)


def test_config_from_dict():
    config_data = {'options': {'some_option': 'some_option_value'},
                   'defaults': {'some_default_key': 'some_default_value'},
                   }

    _config = config.Config.from_dict(config_data)
    assert_object(_config)

    assert _config.options['some_option'] == 'some_option_value'
    assert _config.defaults['some_default_key'] == 'some_default_value'


def test_config_as_dict_empty():
    _config = config.Config()
    config_data = _config.as_dict()

    assert isinstance(config_data, dict)
    assert set(config_data.keys()) == set(CONFIG_SECTIONS)


def test_config_as_dict():
    orig_config_data = {
        'defaults': {'some_default_key': 'some_default_value'},
        'servers': [{'url': 'some_url_value'}],
        'content_roots': [],
        'options': {'some_option': 'some_option_value'},
    }
    _config = config.Config.from_dict(orig_config_data)

    config_data = _config.as_dict()
    assert isinstance(config_data, dict)

    assert set(config_data.keys()) == set(CONFIG_SECTIONS)

    assert config_data == orig_config_data


def test_config_as_dict_from_partial_dict():
    orig_config_data = {
        'defaults': {'some_default_key': 'some_default_value'},
        'servers': [{'url': 'some_url_value'}],
    }
    _config = config.Config.from_dict(orig_config_data)

    config_data = _config.as_dict()
    assert isinstance(config_data, dict)

    assert set(config_data.keys()) == set(CONFIG_SECTIONS)

    assert config_data['defaults'] == orig_config_data['defaults']
    assert config_data['servers'] == orig_config_data['servers']

    assert isinstance(config_data['options'], dict)
    assert config_data['options'] == {}

    assert isinstance(config_data['content_roots'], list)
    assert config_data['content_roots'] == []
