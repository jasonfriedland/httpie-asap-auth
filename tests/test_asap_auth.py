from httpie_asap_auth import AsapAuth


def test_parse_config(asap_config_file):
    asap_config = AsapAuth.parse_config(asap_config_file)

    assert asap_config.iss == 'webapp/admin'
    assert asap_config.kid == 'webapp/admin/dev.pem'
    assert 'asapservice' in asap_config.aud
    assert asap_config.private_key == 'PEM-encoded-key-goes-here'
