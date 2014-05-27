#!/usr/bin/env python

"""Setup file for datastore api"""

from setuptools import setup, find_packages


VERSION = (0, 1, '0dev')

setup(
    name='datastore-api',
    version='.'.join([str(x) for x in VERSION]),
    description="Filedepot API",
    author='Arnaud Porterie',
    author_email='arnaud.porterie@gmail.com',

    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['datastore'],

    install_requires=[
        "flask == 0.10.1",
        "Flask-Bcrypt == 0.5.2",
        "Flask-Login == 0.2.7",
        "itsdangerous == 0.23",
        "pycrypto == 2.6.1",
        "pytz == 2012g",
        "PyYAML == 3.10",
        "scrypt == 0.6.1"
    ],

    dependency_links=[
        # Flask Login 0.1.3 + fix for JSON serialization (see #59)
        "https://github.com/maxcountryman/flask-login/tarball/master/330843d#egg=Flask-Login-0.1.3fixed",
    ],
)
