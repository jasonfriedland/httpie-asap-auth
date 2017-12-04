"""
ASAP Auth plugin for HTTPie.
"""
from __future__ import print_function

import json
import sys

from collections import namedtuple
import atlassian_jwt_auth

from httpie import ExitStatus
from httpie.plugins import AuthPlugin


__version__ = '0.0.4'
__author__ = 'Jason Friedland'
__licence__ = 'MIT'


class AsapAuth:
    """
    Implements ASAP Auth.
    """
    AsapConfig = namedtuple('AsapConfig', ['iss', 'kid', 'aud', 'sub', 'private_key'])

    def __init__(self, asap_config_file):
        asap_config = self.parse_config(asap_config_file)
        self.iss = asap_config.iss
        self.kid = asap_config.kid
        self.aud = asap_config.aud
        self.sub = asap_config.sub
        self.private_key = asap_config.private_key

    def __call__(self, request):
        kwargs = {}
        if self.sub is not None:
            kwargs = {'additional_claims': {'sub': self.sub}}
        signer = atlassian_jwt_auth.create_signer(self.iss, self.kid, self.private_key)
        token = signer.generate_jwt(self.aud, **kwargs)

        request.headers['Authorization'] = 'Bearer {}'.format(token.decode('utf-8'))

        return request

    @staticmethod
    def parse_config(asap_config_file):
        """
        Parse ``asap_config_file`` JSON and return the config required
        to make a valid ASAP/JWT request.
        """
        try:
            with open(asap_config_file) as f:
                config = json.load(f)
        except IOError:
            print('file not found: {}'.format(asap_config_file), file=sys.stderr)
            sys.exit(ExitStatus.PLUGIN_ERROR)
        except ValueError:
            print('invalid JSON config: {}'.format(asap_config_file), file=sys.stderr)
            sys.exit(ExitStatus.PLUGIN_ERROR)

        try:
            asap_config = AsapAuth.AsapConfig(
                # Required:
                iss=config['issuer'], aud=config['audience'], kid=config['kid'],
                private_key=config['privateKey'],
                # Optional:
                sub=config.get('sub')
            )
        except (ValueError, AttributeError, KeyError):
            print('malformed JSON config: {}'.format(asap_config_file), file=sys.stderr)
            sys.exit(ExitStatus.PLUGIN_ERROR)

        return asap_config


class AsapAuthPlugin(AuthPlugin):
    """
    ASAP Auth plugin for HTTPie.
    """
    name = 'ASAP Auth'
    auth_type = 'asap'
    description = 'See: https://s2sauth.bitbucket.io/spec/ for details.'

    # Require but don't parse auth
    auth_require = True
    auth_parse = False
    prompt_password = False

    def get_auth(self, username=None, password=None):
        """
        Get ASAP Auth.

        NB. the --auth, -a option is used as the file path to the ASAP config, and
            is accessible in self.raw_auth.
        """
        return AsapAuth(self.raw_auth)
