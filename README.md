httpie-asap-auth
================

ASAP Auth plugin for [HTTPie](https://httpie.org/).


Installation
------------

    $ python setup.py install


You should now see `asap` under `--auth-type` in the `$ http --help` output.


Usage
-----

    $ http --auth-type=asap --auth=path/to/asap.config http://example.com/
