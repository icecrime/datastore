"""Password hashing and verification helpers.
"""

from flask.ext.bcrypt import Bcrypt

from datastore.api import app


# Wrap the application object in a Bcrypt
bcrypt = Bcrypt(app)


def hash_password(password):
    return bcrypt.generate_password_hash(password), None


def verify_password(hashed_password, salt, attempt):
    return bcrypt.check_password_hash(hashed_password, attempt)
