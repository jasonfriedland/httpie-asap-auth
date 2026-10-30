import json

import jwt
import pytest
from cryptography.exceptions import UnsupportedAlgorithm
from httpie.status import ExitStatus
from requests.models import Request

from httpie_asap_auth import AsapAuthEnvPlugin, AsapAuthPlugin


@pytest.fixture
def config(asap_config_file):
    with open(asap_config_file) as source:
        return json.load(source)


def config_auth(tmp_path, config):
    path = tmp_path / "asap.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    plugin = AsapAuthPlugin()
    plugin.raw_auth = str(path)
    return plugin.get_auth()


def assert_error(capsys, operation, message):
    with pytest.raises(SystemExit) as error:
        operation()
    assert error.value.code == ExitStatus.PLUGIN_ERROR
    assert message in capsys.readouterr().err


@pytest.mark.parametrize("value", [None, [], False, 0, "", [1], True, 2, "text"])
def test_nonobject_config(tmp_path, capsys, value):
    assert_error(capsys, lambda: config_auth(tmp_path, value), "expected dict")


@pytest.mark.parametrize("field", ["issuer", "kid", "audience", "privateKey"])
def test_missing_field(tmp_path, capsys, config, field):
    del config[field]
    assert_error(capsys, lambda: config_auth(tmp_path, config), field)


@pytest.mark.parametrize("field", ["issuer", "kid", "privateKey", "sub"])
@pytest.mark.parametrize("value", [None, "", "  ", 1, [], {}])
def test_invalid_string(tmp_path, capsys, config, field, value):
    config[field] = value
    assert_error(capsys, lambda: config_auth(tmp_path, config), field)


@pytest.mark.parametrize("value", [None, "", " ", [], [""], ["a", " "], [1], {}, 1])
def test_invalid_audience(tmp_path, capsys, config, value):
    config["audience"] = value
    assert_error(capsys, lambda: config_auth(tmp_path, config), "audience")


@pytest.mark.parametrize("audience", [" webapp ", [" webapp "]])
def test_audience_normalization(tmp_path, config, public_key, audience):
    config["audience"] = audience
    request = config_auth(tmp_path, config)(Request())
    token = request.headers["Authorization"].split()[1]
    claims = jwt.decode(token, public_key, algorithms=["RS256"], audience="webapp")
    assert claims["aud"] == ("webapp" if isinstance(audience, str) else ["webapp"])


@pytest.mark.parametrize("absolute", [False, True])
def test_private_key_file(tmp_path, config, public_key, monkeypatch, absolute):
    key = tmp_path / "private.pem"
    key.write_text(config.pop("privateKey"), encoding="utf-8")
    config["privateKeyFile"] = str(key) if absolute else key.name
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    request = config_auth(tmp_path, config)(Request())
    jwt.decode(
        request.headers["Authorization"].split()[1],
        public_key,
        algorithms=["RS256"],
        audience="webapp",
    )


def test_conflicting_key_sources(tmp_path, capsys, config):
    config["privateKeyFile"] = "private.pem"
    assert_error(capsys, lambda: config_auth(tmp_path, config), "exactly one")


@pytest.mark.parametrize("value", ["", None, 123])
def test_invalid_key_file_path(tmp_path, capsys, config, value):
    del config["privateKey"]
    config["privateKeyFile"] = value
    assert_error(capsys, lambda: config_auth(tmp_path, config), "privateKeyFile")


@pytest.mark.parametrize("contents", [None, b"\xff", b""])
def test_unreadable_key_file(tmp_path, capsys, config, contents):
    del config["privateKey"]
    config["privateKeyFile"] = "private.pem"
    if contents is not None:
        (tmp_path / "private.pem").write_bytes(contents)
    assert_error(capsys, lambda: config_auth(tmp_path, config), "privateKey")


def test_config_encoding(tmp_path, capsys):
    path = tmp_path / "asap.json"
    path.write_bytes(b"\xff")
    assert_error(capsys, lambda: AsapAuthPlugin.parse_config_file(path), "invalid JSON")


@pytest.mark.parametrize(
    "auth",
    [
        "",
        " ",
        ":subject",
        "foo,,bar",
        ",foo",
        "foo,",
        "foo:",
        "foo: ",
        "{broken",
        "{}",
        '{"audience": []}',
        '{"audience":"foo","sub":null}',
    ],
)
def test_invalid_auth(capsys, auth):
    assert_error(capsys, lambda: AsapAuthEnvPlugin.parse_auth(auth), "")


@pytest.mark.parametrize(
    "auth,expected",
    [
        ("foo, bar:subject:part", (["foo", "bar"], "subject:part")),
        (
            ' {"audience":["https://service.example","urn:foo,bar"],"sub":"person"}',
            (["https://service.example", "urn:foo,bar"], "person"),
        ),
        ('{"audience":"urn:foo"}', ("urn:foo", None)),
    ],
)
def test_auth_forms(auth, expected):
    assert AsapAuthEnvPlugin.parse_auth(auth) == expected


@pytest.mark.parametrize("field", ["ASAP_PRIVATE_KEY", "ASAP_ISSUER"])
@pytest.mark.parametrize("value", [None, "", " "])
def test_invalid_env(capsys, field, value):
    env = {"ASAP_PRIVATE_KEY": "key", "ASAP_ISSUER": "issuer"}
    if value is None:
        del env[field]
    else:
        env[field] = value
    assert_error(
        capsys, lambda: AsapAuthEnvPlugin.construct_signer_from_env(env), field
    )


def test_auth_validated_before_credentials(monkeypatch, capsys):
    monkeypatch.delenv("ASAP_PRIVATE_KEY", raising=False)
    plugin = AsapAuthEnvPlugin()
    plugin.raw_auth = ":subject"
    assert_error(capsys, plugin.get_auth, "audience")


@pytest.mark.parametrize("mode", ["asap", "asapenv"])
def test_malformed_credentials_are_sanitized(
    tmp_path, capsys, config, monkeypatch, mode
):
    secret = "SENSITIVE_INVALID_PRIVATE_KEY"
    if mode == "asap":
        config["privateKey"] = secret
        auth = config_auth(tmp_path, config)
    else:
        monkeypatch.setenv("ASAP_PRIVATE_KEY", secret)
        monkeypatch.setenv("ASAP_ISSUER", "issuer")
        plugin = AsapAuthEnvPlugin()
        plugin.raw_auth = "audience"
        auth = plugin.get_auth()
    with pytest.raises(SystemExit) as error:
        auth(Request())
    assert error.value.code == ExitStatus.PLUGIN_ERROR
    stderr = capsys.readouterr().err
    assert "unable to sign ASAP token" in stderr
    assert secret not in stderr


@pytest.mark.parametrize(
    "error", [ValueError, TypeError, UnsupportedAlgorithm, jwt.InvalidKeyError]
)
def test_expected_signing_errors(tmp_path, capsys, config, monkeypatch, error):
    auth = config_auth(tmp_path, config)

    def fail(*args, **kwargs):
        raise error("SENSITIVE")

    monkeypatch.setattr(auth, "_get_header_value", fail)
    with pytest.raises(SystemExit) as caught:
        auth(Request())
    assert caught.value.code == ExitStatus.PLUGIN_ERROR
    stderr = capsys.readouterr().err
    assert "unable to sign" in stderr
    assert "SENSITIVE" not in stderr


def test_unexpected_signing_errors_propagate(tmp_path, config, monkeypatch):
    auth = config_auth(tmp_path, config)

    def fail(*args, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr(auth, "_get_header_value", fail)
    with pytest.raises(RuntimeError):
        auth(Request())
