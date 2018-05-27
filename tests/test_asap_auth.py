import pytest

from requests.models import Request
from httpie_asap_auth import AsapAuthPlugin
import jwt


def test_config_file(public_key, asap_config_file):
    payload = generate_and_decode_token(public_key, asap_config_file)
    assert payload.get("iss") == "webapp/admin"
    assert payload.get("sub") == "administration"
    assert payload.get("aud") == ["webapp"]


def test_config_file_no_sub(public_key, asap_config_file_no_sub):
    payload = generate_and_decode_token(public_key, asap_config_file_no_sub)
    assert payload.get("iss") == "webapp/admin"
    assert payload.get("aud") == ["webapp"]
    assert payload.get("sub") == "webapp/admin"


def test_parse_missing_config():
    with pytest.raises(SystemExit):
        get_auth("does/not/exist")


def test_parse_broken_config(broken_asap_config_file):
    with pytest.raises(SystemExit):
        get_auth(broken_asap_config_file)


def test_parse_invalid_config(invalid_asap_config_file):
    with pytest.raises(SystemExit):
        get_auth(invalid_asap_config_file)


def test_parse_invalid_json_config(invalid_json_asap_config_file):
    with pytest.raises(SystemExit):
        get_auth(invalid_json_asap_config_file)


def get_auth(config_file):
    plugin = AsapAuthPlugin()
    plugin.raw_auth = config_file
    return plugin.get_auth()


def generate_and_decode_token(public_key, config_file):
    request = get_auth(config_file)(Request())

    assert "Authorization" in request.headers
    (authtype, token) = request.headers["Authorization"].decode("utf-8").split()
    assert authtype == "Bearer"
    return jwt.decode(token, public_key, algorithms=["RS256"], audience="webapp")
