httpie-asap-auth
================

[![PyPi Package](https://img.shields.io/pypi/v/httpie-asap-auth.svg)](https://pypi.python.org/pypi/httpie-asap-auth) [![Build Status](https://travis-ci.org/jasonfriedland/httpie-asap-auth.svg?branch=master)](https://travis-ci.org/jasonfriedland/httpie-asap-auth)

[ASAP](https://s2sauth.bitbucket.io/) Auth plugin for [HTTPie](https://httpie.org/).


Installation
------------

    $ pip install httpie-asap-auth


You should now see `asap` and `asapenv` under `--auth-type` in the `$ http --help` output.


Usage
-----

    $ http --auth-type=asap --auth=path/to/asap.config http://example.com/

OR, to read from environment variables:

    $ http --auth-type=asapenv --auth=audience[:subject] http://example.com/


Example ASAP Config
-------------------

Store your ASAP config in a file following this format:

```
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
NB. the subject (`sub` field) is optional. 

Example environment variables
-----------------------------

    ASAP_PRIVATE_KEY=data:application/pkcs8;kid=webapp;base64,...
    ASAP_ISSUER=webapp/admin

(if you have multiple audiences, you should comma separate them)

How to generate a data uri from an RSA private key pem file
-----------------------------------------------------------

    #!/bin/sh

    # Usage: convert-pem-to-asap-data-uri.sh privatekey.pem

    KID=$(echo "$1" | sed 's|/|%2F|g')
    KEY=$(openssl pkcs8 -topk8 -inform PEM -outform DER -in "$1" -nocrypt | base64 | tr '\n' ' ' | sed 's| ||g')

    echo "data:application/pkcs8;kid=$KID;base64,$KEY"

(thanks to Brian McKenna)
