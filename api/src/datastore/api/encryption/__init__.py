"""Encryption package implements the different ways to handle encryption.

Possible implementations:
    - bcrypt: use bcrypt algorithm through Flask-Bcrypt
    - scrypt: use scrypt implementation
    - nil: no encryption, used for testing purposes

"""


def from_config(app, config):
    """Import the appropriate encryption module according to the config."""
    encryption = config.auth.get('encryption', 'bcrypt')
    return __import__('%s.enc_%s' % (__name__, encryption), fromlist=[None])
