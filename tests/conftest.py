import os
import pytest


@pytest.fixture(scope='session')
def asap_config_file():
    return os.path.join(os.path.dirname(__file__), 'data', 'asap.config')


@pytest.fixture(scope='session')
def asap_config_file_no_sub():
    return os.path.join(os.path.dirname(__file__), 'data', 'asap.config.nosub')


@pytest.fixture(scope='session')
def broken_asap_config_file():
    return os.path.join(os.path.dirname(__file__), 'data', 'asap.config.broken')


@pytest.fixture(scope='session')
def invalid_asap_config_file():
    return os.path.join(os.path.dirname(__file__), 'data', 'asap.config.invalid')
