"""Nil passwod hashing to speed up unit tests.
"""


def hash_password(password):
    return password, None


def verify_password(hashed_password, salt, attempt):
    return hashed_password == attempt
