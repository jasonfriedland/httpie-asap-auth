import os
import pytest


@pytest.fixture(scope='session')
def asap_config_file():
    return os.path.join(os.path.dirname(__file__), 'data', 'asap.config')
