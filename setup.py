"""
setup.py for httpie-asap-auth.
"""
from setuptools import setup


setup(
    name="httpie-asap-auth",
    description="ASAP Auth plugin for HTTPie.",
    long_description="An ASAP (JWT-based) Auth plugin for HTTPie. "
    "See: https://s2sauth.bitbucket.io/spec/ for details.",
    version="0.1.2",
    author="Jason Friedland",
    author_email="jason@friedland.id.au",
    license="MIT",
    url="https://github.com/jasonfriedland/httpie-asap-auth",
    download_url="https://github.com/jasonfriedland/httpie-asap-auth",
    py_modules=["httpie_asap_auth"],
    zip_safe=False,
    entry_points={
        "httpie.plugins.auth.v1": [
            "httpie_asap_auth = httpie_asap_auth:AsapAuthPlugin",
            "httpie_asap_auth_env = httpie_asap_auth:AsapAuthEnvPlugin",
        ]
    },
    install_requires=["httpie>=2.0.0", "atlassian-jwt-auth>=5.0.3"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Environment :: Plugins",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
)
