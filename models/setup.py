#!/usr/bin/env python

"""Setup file for datastore models"""

import sys

from setuptools import setup, find_packages


VERSION = (0, 1, '0dev')

# Module argparse is only standard since Python 2.7.
install_requires = ["SQLAlchemy == 0.8.3"]
if sys.version_info[:2] < (2, 7):
    install_requires.append("argparse")

setup(
    name='datastore-models',
    version='.'.join([str(x) for x in VERSION]),
    description="Filedepot models",
    author='Arnaud Porterie',
    author_email='arnaud.porterie@gmail.com',

    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['datastore'],

    install_requires=install_requires,
)
