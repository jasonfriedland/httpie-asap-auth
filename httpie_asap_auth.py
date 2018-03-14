"""
ASAP Auth plugin for HTTPie.
"""
from __future__ import print_function

import json
import sys
import os

import atlassian_jwt_auth
import atlassian_jwt_auth.key
import atlassian_jwt_auth.signer
import atlassian_jwt_auth.contrib.requests

from httpie import ExitStatus
from httpie.plugins import AuthPlugin


__version__ = '0.0.9'
__author__ = 'Jason Friedland'
__licence__ = 'MIT'


def fatal_plugin_error(message):
    print(message, file=sys.stderr)
    sys.exit(ExitStatus.PLUGIN_ERROR)


class AsapAuthPlugin(AuthPlugin):
    """
    ASAP Auth plugin for HTTPie, reading from config file.
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

        The --auth, -a option is used as the file path to the ASAP config
        (in JSON form). We access this via self.raw_auth rather
        than username/password.

        :param str username: Unused.
        :param str password: Unused.
        :return: atlassian_jwt_auth.contrib.requests.JWTAuth
        """
        (signer, audience, subject) = self.parse_config_file(self.raw_auth)
        return atlassian_jwt_auth.contrib.requests.JWTAuth(
            signer, audience, additional_claims={'sub': subject} if subject else {})

    @staticmethod
    def parse_config_file(asap_config_file):
        """
        Parse ``asap_config_file`` JSON and return the signer.

        :param str asap_config_file: Path to the ASAP config file.

        :return: atlassian_jwt_auth.signer.JWTAuthSigner
        :raises ExitStatus.PLUGIN_ERROR: Invalid config.
        """
        config = None

        try:
            with open(asap_config_file) as f:
                config = json.load(f)
        except IOError:
            fatal_plugin_error('file not readable: {}'.format(asap_config_file))
        except ValueError:
            fatal_plugin_error('invalid JSON config: {}'.format(asap_config_file))

        if config and not isinstance(config, dict):
            fatal_plugin_error('invalid JSON config (expected dict): {}'.format(asap_config_file))

        try:
            return (
                atlassian_jwt_auth.create_signer(config['issuer'], config['kid'], config['privateKey']),
                config['audience'],
                config.get('sub')
            )
        except KeyError as e:
            fatal_plugin_error('expected key in config file: {}'.format(e))


class AsapAuthEnvPlugin(AuthPlugin):
    """
    ASAP Auth plugin for HTTPie, reading from environment.
    """
    name = 'ASAP Auth from environment'
    auth_type = 'asapenv'
    description = 'See: https://s2sauth.bitbucket.io/spec/ for details.'

    # Require but don't parse auth
    auth_require = True
    auth_parse = False
    prompt_password = False

    def get_auth(self, username=None, password=None):
        """
        Get ASAP Auth.

        We use the environment variables ASAP_PRIVATE_KEY (data_uri form) and
        ASAP_ISSUER for ASAP configuration, augmented by --auth, -a (which provides
        audience1,audience2,...:subject). Subjects are optional.

        :param str username: Unused.
        :param str password: Unused.

        :return: atlassian_jwt_auth.contrib.requests.JWTAuth
        """
        signer = self.construct_signer_from_env(os.environ)
        audience, subject = self.parse_auth(self.raw_auth)
        return atlassian_jwt_auth.contrib.requests.JWTAuth(
            signer, audience, additional_claims={'sub': subject} if subject else {})

    @staticmethod
    def construct_signer_from_env(env):
        """
        Returns a new JWT signer initialised using values from the environment.

        :param dict env: A dict holding the shell environment.

        :return: atlassian_jwt_auth.signer.JWTAuthSigner
        :raises ExitStatus.PLUGIN_ERROR: Invalid environment.
        """
        try:
            provider = atlassian_jwt_auth.key.DataUriPrivateKeyRetriever(env['ASAP_PRIVATE_KEY'])
            return atlassian_jwt_auth.signer.JWTAuthSigner(env['ASAP_ISSUER'], provider)
        except KeyError as e:
            fatal_plugin_error('missing {} in environment'.format(e))

    @staticmethod
    def parse_auth(auth):
        """
        Parse the ``auth`` arg and return the audience and subject.

        >>> AsapAuthEnvPlugin.parse_auth("foo,bar:baz")
        (['foo', 'bar'], 'baz')

        >>> AsapAuthEnvPlugin.parse_auth(":baz")
        ([''], 'baz')

        >>> AsapAuthEnvPlugin.parse_auth("foo")
        (['foo'], None)

        :param str auth: The ``auth`` arg passed on the CLI. Contains the audience and subject.
        :return: tuple(List[str], str)
        """
        auth = auth.split(':', 1)

        if len(auth) == 1:
            audience, subject = auth[0], None
        else:
            audience, subject = auth

        return audience.split(','), subject
