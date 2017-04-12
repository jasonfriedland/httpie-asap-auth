"""
setup.py for httpie-asap-auth.
"""
from setuptools import setup


setup(
    name='httpie-asap-auth',
    description='ASAP Auth plugin for HTTPie.',
    long_description=open('README.md').read().strip(),
    version='0.0.1',
    author='Jason Friedland',
    author_email='jason@friedland.id.au',
    license='MIT',
    url='https://github.com/jasonfriedland/httpie-asap-auth',
    download_url='https://github.com/jasonfriedland/httpie-asap-auth',
    py_modules=['httpie_asap_auth'],
    zip_safe=False,
    entry_points={
        'httpie.plugins.auth.v1': [
            'httpie_asap_auth = httpie_asap_auth:AsapAuthPlugin'
        ]
    },
    install_requires=[
        'httpie>=0.9.9',
        'atlassian-jwt-auth>=2.10.2'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Environment :: Plugins',
        'License :: OSI Approved :: MIT License',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities'
    ],
)
