import os
import random

import sys
if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest


# Update environment before importing the api.
os.environ['DATASTORE_STORAGE_ROOT'] = 'api/tests/store/'
os.environ['DATASTORE_API_CONFIG_FILE'] = 'config_test.yaml'


# Initialize the random number generator.
random.seed()


# Import all test fixtures
from test_chunked import *
from test_encryption import *
from test_file_store import *
from test_files import *
from test_fileops import *
from test_users import *


def main():
    unittest.main(__name__)
