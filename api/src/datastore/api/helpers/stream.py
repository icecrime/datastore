import hashlib
import struct

from flask import request

from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Util import Counter


class ChecksumCalcStream(object):

    def __init__(self, stream):
        self._stream = stream
        self.hash = hashlib.sha1()

    def read(self, *args, **kwargs):
        rv = self._stream.read(*args, **kwargs)
        self.hash.update(rv)
        return rv

    def readline(self, *args, **kwargs):  # pragma: no cover
        rv = self._stream.readline(*args, **kwargs)
        self.hash.update(rv)
        return rv


class AESDecryptionStream(object):

    def __init__(self, stream, key, iv):
        self._countr = Counter.new(128, initial_value=iv)
        self._cipher = AES.new(key, AES.MODE_CTR, counter=self._countr)
        self._stream = stream

    def read(self, *args, **kwargs):
        rv = self._stream.read(*args, **kwargs)
        return self._cipher.decrypt(rv)

    def readline(self, *args, **kwargs):  # pragma: no cover
        rv = self._stream.readline(*args, **kwargs)
        return self._cipher.decrypt(rv)


class AESEncryptionStream(object):

    def __init__(self, stream, key):
        self.IV = self._generate_IV()
        self._countr = Counter.new(128, initial_value=self.IV)
        self._cipher = AES.new(key, AES.MODE_CTR, counter=self._countr)
        self._stream = stream

    def read(self, *args, **kwargs):
        rv = self._stream.read(*args, **kwargs)
        return self._cipher.encrypt(rv)

    def readline(self, *args, **kwargs):  # pragma: no cover
        rv = self._stream.readline(*args, **kwargs)
        return self._cipher.encrypt(rv)

    @staticmethod
    def _generate_IV():
        randstr = Random.new().read(4)
        return struct.unpack("i", randstr)[0]

def install_stream(decorator, *args, **kwargs):
    env = request.environ
    stream = decorator(env['wsgi.input'], *args, **kwargs)
    env['wsgi.input'] = stream
    return stream
