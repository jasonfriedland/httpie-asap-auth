# httpie-asap-auth

[![PyPi Package](https://img.shields.io/pypi/v/httpie-asap-auth.svg)](https://pypi.python.org/pypi/httpie-asap-auth)
[![PyPi Versions](https://pypi-camo.freetls.fastly.net/73d938bb8ffa2fa754351c502e49417e987e6a2e/68747470733a2f2f696d672e736869656c64732e696f2f707970692f707976657273696f6e732f6874747069652d617361702d617574682e737667)](https://pypi.python.org/pypi/httpie-asap-auth)
[![Actions Status](https://github.com/jasonfriedland/httpie-asap-auth/workflows/test/badge.svg)](https://github.com/jasonfriedland/httpie-asap-auth/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

An [ASAP](https://s2sauth.bitbucket.io/) authentication plugin for [HTTPie](https://httpie.org/).

## Installation

Python 3.8 through Python 3.15 are supported.

    pip install httpie-asap-auth

You should now see `asap` and `asapenv` under `--auth-type` in the `$ http --help` output.

## Usage

    http --auth-type=asap --auth=path/to/asap.config http://example.com/

Alternatively, to read from environment variables:

    http --auth-type=asapenv --auth=audience[:subject] http://example.com/

Separate multiple audiences with commas.

## Example ASAP Config

Store your ASAP configuration in a file using the following format:

```json
{
    "issuer": "webapp/admin",
    "kid": "webapp/admin/dev.pem",
    "audience": [
        "webapp"
    ],
    "sub": "administration",
    "privateKey": "-----BEGIN RSA PRIVATE KEY-----\n ... \n-----END RSA PRIVATE KEY-----"
}
```

Note: The subject (`sub` field) is optional.

## Example Environment Variables

    ASAP_PRIVATE_KEY=data:application/pkcs8;kid=webapp;base64,...
    ASAP_ISSUER=webapp/admin

## Generate a Data URI

Generate a data URI containing a PKCS#8 key from an RSA private key in PEM format:

```shell
#!/bin/sh

# Usage: $0 privatekey.pem

KID=$(echo "$1" | sed 's|/|%2F|g')
KEY=$(openssl pkcs8 -topk8 -inform PEM -outform DER -in "$1" -nocrypt | base64 | tr '\n' ' ' | sed 's| ||g')

echo "data:application/pkcs8;kid=$KID;base64,$KEY"
```

Thanks to Brian McKenna.

## Development

[Install uv](https://docs.astral.sh/uv/getting-started/installation/), then create
the development environment from the committed lockfile:

    make sync

Run the test suite and formatter with the locked dependencies:

    make test
    make fmt

The formatter runs on Python 3.14 while preserving Python 3.8-compatible
syntax.

Upgrade all dependencies and review the resulting lockfile with:

    make upgrade

Build the source and wheel distributions with:

    make build

Maintainers can publish the built distributions after configuring uv's PyPI
credentials:

    make publish
