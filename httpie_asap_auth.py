"""
ASAP Auth plugin for HTTPie.
"""

from __future__ import print_function

import json
import sys
import os
from pathlib import Path

import atlassian_jwt_auth
import atlassian_jwt_auth.key
import atlassian_jwt_auth.signer
import atlassian_jwt_auth.contrib.requests

from httpie.status import ExitStatus
from httpie.plugins import AuthPlugin
from cryptography.exceptions import UnsupportedAlgorithm
from jwt.exceptions import InvalidKeyError

__author__ = "Jason Friedland"
__licence__ = "MIT"


def fatal_plugin_error(message):
    print(message, file=sys.stderr)
    sys.exit(ExitStatus.PLUGIN_ERROR)


SIGNING_ERRORS = (ValueError, TypeError, UnsupportedAlgorithm, InvalidKeyError)


def required_string(value, field):
    if not isinstance(value, str) or not value.strip():
        fatal_plugin_error("{} must be a nonempty string".format(field))
    return value


def parse_audience(value):
    if isinstance(value, str):
        return required_string(value, "audience").strip()
    if not isinstance(value, list) or not value:
        fatal_plugin_error("audience must be a nonempty string or list of strings")
    return [required_string(item, "audience entry").strip() for item in value]


def parse_subject(config):
    return required_string(config["sub"], "sub") if "sub" in config else None


class SafeJWTAuth(atlassian_jwt_auth.contrib.requests.JWTAuth):
    """Report expected credential failures when the lazy signer is invoked."""

    def __call__(self, request):
        try:
            return super().__call__(request)
        except SIGNING_ERRORS:
            fatal_plugin_error(
                "unable to sign ASAP token: check the private key and key identifier"
            )


class AsapAuthPlugin(AuthPlugin):
    """
    ASAP Auth plugin for HTTPie, reading from config file.
    """

    name = "ASAP Auth"
    auth_type = "asap"
    description = "See: https://s2sauth.bitbucket.io/spec/ for details."

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
        signer, audience, subject = self.parse_config_file(self.raw_auth)
        return SafeJWTAuth(
            signer, audience, additional_claims={"sub": subject} if subject else {}
        )

    @staticmethod
    def parse_config_file(asap_config_file):
        """
        Parse ``asap_config_file`` JSON and return the signer.

        :param str asap_config_file: Path to the ASAP config file.

        :return: Tuple of signer, audience and optional subject.
        :raises SystemExit: Invalid config.
        """
        try:
            with open(asap_config_file, encoding="utf-8") as f:
                config = json.load(f)
        except IOError:
            fatal_plugin_error("file not readable: {}".format(asap_config_file))
        except ValueError:
            fatal_plugin_error("invalid JSON config: {}".format(asap_config_file))

        if not isinstance(config, dict):
            fatal_plugin_error(
                "invalid JSON config (expected dict): {}".format(asap_config_file)
            )

        issuer = required_string(config.get("issuer"), "issuer")
        kid = required_string(config.get("kid"), "kid")
        audience = parse_audience(config.get("audience"))
        subject = parse_subject(config)
        if ("privateKey" in config) == ("privateKeyFile" in config):
            fatal_plugin_error("configure exactly one of privateKey and privateKeyFile")
        if "privateKeyFile" in config:
            key_path = Path(asap_config_file).parent / required_string(
                config["privateKeyFile"], "privateKeyFile"
            )
            try:
                private_key = key_path.read_text(encoding="utf-8")
            except (OSError, ValueError):
                fatal_plugin_error("privateKeyFile is not readable as UTF-8")
        else:
            private_key = config["privateKey"]
        required_string(private_key, "privateKey")
        try:
            signer = atlassian_jwt_auth.create_signer(issuer, kid, private_key)
        except SIGNING_ERRORS:
            fatal_plugin_error("invalid ASAP credentials: check privateKey and kid")
        return signer, audience, subject


class AsapAuthEnvPlugin(AuthPlugin):
    """
    ASAP Auth plugin for HTTPie, reading from environment.
    """

    name = "ASAP Auth from environment"
    auth_type = "asapenv"
    description = "See: https://s2sauth.bitbucket.io/spec/ for details."

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
        audience, subject = self.parse_auth(self.raw_auth)
        signer = self.construct_signer_from_env(os.environ)
        return SafeJWTAuth(
            signer, audience, additional_claims={"sub": subject} if subject else {}
        )

    @staticmethod
    def construct_signer_from_env(env):
        """
        Returns a new JWT signer initialised using values from the environment.

        :param dict env: A dict holding the shell environment.

        :return: atlassian_jwt_auth.signer.JWTAuthSigner
        :raises SystemExit: Invalid environment.
        """
        private_key = required_string(env.get("ASAP_PRIVATE_KEY"), "ASAP_PRIVATE_KEY")
        issuer = required_string(env.get("ASAP_ISSUER"), "ASAP_ISSUER")
        try:
            provider = atlassian_jwt_auth.key.DataUriPrivateKeyRetriever(private_key)
            return atlassian_jwt_auth.signer.JWTAuthSigner(issuer, provider)
        except SIGNING_ERRORS:
            fatal_plugin_error("invalid ASAP credentials: check ASAP_PRIVATE_KEY")

    @staticmethod
    def parse_auth(auth):
        """
        Parse the ``auth`` arg and return the audience and subject.

        >>> AsapAuthEnvPlugin.parse_auth("foo,bar:baz")
        (['foo', 'bar'], 'baz')

        >>> AsapAuthEnvPlugin.parse_auth("foo, bar")
        (['foo', 'bar'], None)

        >>> AsapAuthEnvPlugin.parse_auth("foo")
        (['foo'], None)

        :param str auth: The ``auth`` arg passed on the CLI. Contains the audience and subject.
        :return: Tuple of audience (string or list) and optional subject.
        """
        auth = required_string(auth, "auth")
        if auth.lstrip().startswith("{"):
            try:
                config = json.loads(auth)
            except ValueError:
                fatal_plugin_error("invalid JSON auth object")
            return parse_audience(config.get("audience")), parse_subject(config)

        auth = auth.split(":", 1)

        if len(auth) == 1:
            audience, subject = auth[0], None
        else:
            audience, subject = auth
            subject = required_string(subject, "sub")

        return parse_audience(audience.split(",")), subject
