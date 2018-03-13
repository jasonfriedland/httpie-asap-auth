import os
import pytest

def datapath(fname):
    return os.path.join(os.path.dirname(__file__), 'data', fname)


@pytest.fixture(scope='session')
def asap_config_file():
    return datapath('asap.config')


@pytest.fixture(scope='session')
def asap_config_file_no_sub():
    return datapath('asap.config.nosub')


@pytest.fixture(scope='session')
def broken_asap_config_file():
    return datapath('asap.config.broken')


@pytest.fixture(scope='session')
def invalid_asap_config_file():
    return datapath('asap.config.invalid')

@pytest.fixture(scope='session')
def public_key():
    with open(datapath('publickey.pem')) as f:
        return f.read()

@pytest.fixture(scope='session')
def data_uri_private_key():
    with open(datapath('privatekey.datauri')) as f:
        return f.read()
