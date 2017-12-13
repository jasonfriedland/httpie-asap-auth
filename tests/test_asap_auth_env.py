import pytest

from requests.models import Request
from httpie_asap_auth import AsapAuthEnvPlugin
import jwt


def test_env(public_key, data_uri_private_key, monkeypatch):
    monkeypatch.setenv('ASAP_PRIVATE_KEY', data_uri_private_key)
    monkeypatch.setenv('ASAP_ISSUER', 'webapp/admin')
    payload = generate_and_decode_token(public_key, 'webapp,webapp2:administration')
    assert payload.get('iss') == 'webapp/admin'
    assert payload.get('sub') == 'administration'
    assert payload.get('aud') == ['webapp', 'webapp2']


def test_env_no_sub(public_key, data_uri_private_key, monkeypatch):
    monkeypatch.setenv('ASAP_PRIVATE_KEY', data_uri_private_key)
    monkeypatch.setenv('ASAP_ISSUER', 'webapp/admin')
    payload = generate_and_decode_token(public_key, 'webapp')
    assert payload.get('iss') == 'webapp/admin'
    assert payload.get('aud') == ['webapp']
    assert payload.get('sub') == 'webapp/admin'


def test_env_invalid(monkeypatch):
    monkeypatch.delenv('ASAP_PRIVATE_KEY', raising=False)
    with pytest.raises(SystemExit):
        get_auth('foo')


def get_auth(raw_auth):
    plugin = AsapAuthEnvPlugin()
    plugin.raw_auth = raw_auth
    return plugin.get_auth()


def generate_and_decode_token(public_key, raw_auth=None):
    request = get_auth(raw_auth)(Request())

    assert 'Authorization' in request.headers
    (authtype, token) = request.headers['Authorization'].decode('utf-8').split()
    assert authtype == 'Bearer'
    return jwt.decode(token, public_key, algorithms=['RS256'], audience='webapp')
