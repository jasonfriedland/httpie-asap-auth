"""
ASAP Auth plugin for HTTPie.
"""
from __future__ import print_function

import json
import sys
import os

from collections import namedtuple
import atlassian_jwt_auth
import atlassian_jwt_auth.key
import atlassian_jwt_auth.signer
import atlassian_jwt_auth.contrib.requests

from httpie import ExitStatus
from httpie.plugins import AuthPlugin


__version__ = '0.0.5'
__author__ = 'Jason Friedland'
__licence__ = 'MIT'


def fatal_plugin_error(message):
    print(message, file=sys.stderr)
    sys.exit(ExitStatus.PLUGIN_ERROR)


def process_env(env):
    try:
        provider = atlassian_jwt_auth.key.DataUriPrivateKeyRetriever(env['ASAP_PRIVATE_KEY'])
        return (
            atlassian_jwt_auth.signer.JWTAuthSigner(env['ASAP_ISSUER'], provider),
            env['ASAP_AUDIENCE'].split(','),
            {'sub': env['ASAP_SUBJECT']} if 'ASAP_SUBJECT' in env else {}
        )
    except KeyError as e:
        fatal_plugin_error(
            'missing {} in environment; '
            'did you mean to specify a file using --auth?'.format(e))


def process_config_file(asap_config_file):
    """
    Parse ``asap_config_file`` JSON and return the signer and audience.
    """

    try:
        with open(asap_config_file) as f:
            config = json.load(f)
    except IOError:
        fatal_plugin_error('file not readable: {}'.format(asap_config_file))
    except ValueError:
        fatal_plugin_error('invalid JSON config: {}'.format(asap_config_file))

    if not isinstance(config, dict):
        fatal_plugin_error('config file is not a json object')

    try:
        return (
            atlassian_jwt_auth.create_signer(config['issuer'], config['kid'], config['privateKey']),
            config['audience'],
            {'sub': config['sub']} if 'sub' in config else {}
        )
    except KeyError as e:
        fatal_plugin_error('missing {} in config file'.format(e))


class AsapAuthPlugin(AuthPlugin):
    """
    ASAP Auth plugin for HTTPie.
    """
    name = 'ASAP Auth'
    auth_type = 'asap'
    description = 'See: https://s2sauth.bitbucket.io/spec/ for details.'

    # Require but don't parse auth
    auth_require = False
    auth_parse = False
    prompt_password = False

    def get_auth(self, username=None, password=None):
        """
        Get ASAP Auth.

        If the --auth, -a option is provided, this is used as the file path to
        the ASAP config (in JSON form). We access this via self.raw_auth rather
        than username/password.

        Otherwise, we attempt to use the environment variables ASAP_PRIVATE_KEY
        (in data uri form with key id), ASAP_AUDIENCE, ASAP_ISSUER, and ASAP_SUBJECT
        (if available).
        """
        if self.raw_auth:
            (signer, audience, additional_claims) = process_config_file(self.raw_auth)
        else:
            (signer, audience, additional_claims) = process_env(os.environ)

        return atlassian_jwt_auth.contrib.requests.JWTAuth(
                signer, audience, additional_claims=additional_claims)
