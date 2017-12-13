import pytest

from requests.models import Request
from httpie_asap_auth import AsapAuthPlugin
import jwt


def test_config_file(public_key, asap_config_file):
    payload = generate_and_decode_token(public_key, asap_config_file)
    assert payload.get('iss') == 'webapp/admin'
    assert payload.get('sub') == 'administration'
    assert payload.get('aud') == ['webapp']


def test_config_file_no_sub(public_key, asap_config_file_no_sub):
    payload = generate_and_decode_token(public_key, asap_config_file_no_sub)
    assert payload.get('iss') == 'webapp/admin'
    assert payload.get('aud') == ['webapp']
    assert payload.get('sub') == 'webapp/admin'


def test_parse_missing_config():
    with pytest.raises(SystemExit):
        get_auth('does/not/exist')


def test_parse_broken_config(broken_asap_config_file):
    with pytest.raises(SystemExit):
        get_auth(broken_asap_config_file)


def test_parse_invalid_config(invalid_asap_config_file):
    with pytest.raises(SystemExit):
        get_auth(invalid_asap_config_file)


def test_env(public_key, data_uri_private_key, monkeypatch):
    monkeypatch.setenv('ASAP_PRIVATE_KEY', data_uri_private_key)
    monkeypatch.setenv('ASAP_ISSUER', 'webapp/admin')
    monkeypatch.setenv('ASAP_AUDIENCE', 'webapp')
    monkeypatch.setenv('ASAP_SUBJECT', 'administration')
    payload = generate_and_decode_token(public_key)
    assert payload.get('iss') == 'webapp/admin'
    assert payload.get('sub') == 'administration'
    assert payload.get('aud') == ['webapp']


def test_env_no_sub(public_key, data_uri_private_key, monkeypatch):
    monkeypatch.setenv('ASAP_PRIVATE_KEY', data_uri_private_key)
    monkeypatch.setenv('ASAP_ISSUER', 'webapp/admin')
    monkeypatch.setenv('ASAP_AUDIENCE', 'webapp')
    payload = generate_and_decode_token(public_key)
    assert payload.get('iss') == 'webapp/admin'
    assert payload.get('aud') == ['webapp']
    assert payload.get('sub') == 'webapp/admin'


def test_env_invalid(monkeypatch):
    monkeypatch.delenv('ASAP_PRIVATE_KEY', raising=False)
    with pytest.raises(SystemExit):
        get_auth()


def get_auth(config_file=None):
    plugin = AsapAuthPlugin()
    plugin.raw_auth = config_file
    return plugin.get_auth()


def generate_and_decode_token(public_key, config_file=None):
    request = get_auth(config_file)(Request())

    assert 'Authorization' in request.headers
    (authtype, token) = request.headers['Authorization'].decode('utf-8').split()
    assert authtype == 'Bearer'
    return jwt.decode(token, public_key, algorithms=['RS256'], audience='webapp')
