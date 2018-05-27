import pytest

from requests.models import Request
from httpie_asap_auth import AsapAuth, AsapAuthPlugin


def test_parse_config(asap_config_file):
    asap_config = AsapAuth.parse_config(asap_config_file)

    assert asap_config.iss == "webapp/admin"
    assert asap_config.kid == "webapp/admin/test.pem"
    assert asap_config.sub == "administration"
    assert "webapp" in asap_config.aud
    assert (
        asap_config.private_key
        == "-----BEGIN RSA PRIVATE KEY-----\nMIIBOwIBAAJBAL6LQj1BUFIg4mH3YxZ/SQydmmG4hvm8sv2/XQ//qiq/yAABmAuX\nnPPS7pNMbApOsiW5YPBY4bkQYmBG0xoTXLsCAwEAAQJBALthdY2JqnRptFcFEqOw\nHuVSI90Pu2Ti5d7WDq3KDc0kwYHRs+2RFST6AgKHC50qPdTXZvcl3PHRbKBoX6vS\nsWECIQD2jxx706W05hUgz3V7rgoszwJChWykiKjsObPbJzPf8QIhAMXXD7VY37cZ\n0vSXKSxk95q/ifnucuHNsPK8v596A/NrAiA98Yx1a6H5BckPGi/o57u0sDlgHwdB\nevf9iS2vhHTa8QIgU1d9ro957tBaJd9n4OPHytDVdwwUKTtVR2xr7Oqhr3ECIQDq\nLZIoMx02q77tY0MIT9g0OEeUQaurV0PqpQEHWtb1pA==\n-----END RSA PRIVATE KEY-----"
    )


def test_parse_config_no_sub(asap_config_file_no_sub):
    asap_config = AsapAuth.parse_config(asap_config_file_no_sub)

    assert asap_config.iss == "webapp/admin"
    assert asap_config.kid == "webapp/admin/test.pem"
    assert asap_config.sub is None
    assert "webapp" in asap_config.aud
    assert (
        asap_config.private_key
        == "-----BEGIN RSA PRIVATE KEY-----\nMIIBOwIBAAJBAL6LQj1BUFIg4mH3YxZ/SQydmmG4hvm8sv2/XQ//qiq/yAABmAuX\nnPPS7pNMbApOsiW5YPBY4bkQYmBG0xoTXLsCAwEAAQJBALthdY2JqnRptFcFEqOw\nHuVSI90Pu2Ti5d7WDq3KDc0kwYHRs+2RFST6AgKHC50qPdTXZvcl3PHRbKBoX6vS\nsWECIQD2jxx706W05hUgz3V7rgoszwJChWykiKjsObPbJzPf8QIhAMXXD7VY37cZ\n0vSXKSxk95q/ifnucuHNsPK8v596A/NrAiA98Yx1a6H5BckPGi/o57u0sDlgHwdB\nevf9iS2vhHTa8QIgU1d9ro957tBaJd9n4OPHytDVdwwUKTtVR2xr7Oqhr3ECIQDq\nLZIoMx02q77tY0MIT9g0OEeUQaurV0PqpQEHWtb1pA==\n-----END RSA PRIVATE KEY-----"
    )


def test_parse_missing_config():
    with pytest.raises(SystemExit):
        AsapAuth.parse_config("does/not/exist")


def test_parse_broken_config(broken_asap_config_file):
    with pytest.raises(SystemExit):
        AsapAuth.parse_config(broken_asap_config_file)


def test_parse_invalid_config(invalid_asap_config_file):
    with pytest.raises(SystemExit):
        AsapAuth.parse_config(invalid_asap_config_file)


def test_auth_header(asap_config_file):
    request = AsapAuth(asap_config_file)(Request())
    assert "Authorization" in request.headers
    assert request.headers["Authorization"].startswith("Bearer ")


def test_auth_plugin(asap_config_file):
    plugin = AsapAuthPlugin()
    plugin.raw_auth = asap_config_file
    plugin.get_auth()
