"""Password hashing and verification helpers.
"""

# Required because of scrypt module name conflict.
from __future__ import absolute_import

import base64
import os
import scrypt


def _generate_random_salt():
    salt = os.urandom(64)
    return base64.b64encode(salt)


def _unicode_to_str(u):
    return u if not isinstance(u, unicode) else u.encode('utf-8')


def hash_password(password):
    salt = _generate_random_salt()
    password = _unicode_to_str(password)
    return scrypt.hash(password, salt), salt


def verify_password(hashed_password, salt, attempt):
    attempt = _unicode_to_str(attempt)
    return scrypt.hash(attempt, salt) == hashed_password
