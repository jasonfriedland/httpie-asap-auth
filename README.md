httpie-asap-auth
================

[![Build Status](https://travis-ci.org/jasonfriedland/httpie-asap-auth.svg?branch=master)](https://travis-ci.org/jasonfriedland/httpie-asap-auth)

ASAP Auth plugin for [HTTPie](https://httpie.org/).


Installation
------------

    $ pip install httpie-asap-auth


You should now see `asap` under `--auth-type` in the `$ http --help` output.


Usage
-----

    $ http --auth-type=asap --auth=path/to/asap.config http://example.com/


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
    "privateKey": "-----BEGIN RSA PRIVATE KEY-----\n ... \n-----END RSA PRIVATE KEY-----"
}
```
