"""User_store package implements the different ways to store user accounts.

Possible implementations:
    - db: store user data in database

"""

import importlib


def from_config(app, config):
    """Import the appropriate storage module according to the config."""
    user_store = config.auth.get('user_store', 'db')
    return importlib.import_module('%s.%s' % (__name__, user_store))
