import base64
import os
from . import unittest

from datastore.api.encryption import enc_bcrypt, enc_scrypt


class EncryptionTestCase(object):

    @staticmethod
    def _generate_password():
        return base64.urlsafe_b64encode(os.urandom(64))

    def test_encrypt(self):
        passw = self._generate_password()
        hashp, salt = self.backend.hash_password(passw)
        self.assertIsNotNone(hashp)
        self.assertGreater(len(hashp), 0)

    def test_decrypt_bad(self):
        passw = self._generate_password()
        other = self._generate_password()
        hashp, salt = self.backend.hash_password(passw)
        verify_password = self.backend.verify_password(hashp, salt, other)
        self.assertFalse(verify_password)

    def test_decrypt_good(self):
        passw = self._generate_password()
        hashp, salt = self.backend.hash_password(passw)
        verify_password = self.backend.verify_password(hashp, salt, passw)
        self.assertTrue(verify_password)


class BcryptTestCase(EncryptionTestCase, unittest.TestCase):
    backend = enc_bcrypt


class ScryptTestCase(EncryptionTestCase, unittest.TestCase):
    backend = enc_scrypt
