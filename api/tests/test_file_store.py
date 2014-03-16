import cStringIO
import hashlib
import os.path
import random
import shutil
import tempfile
from . import unittest

from flask import request

# Inject dummy fs_root to avoid error at import time.
from datastore.api import app, config
config.storage['fs_root'] = ''

from datastore.api.helpers import stream
from datastore.api.file_store import fs


class FilesystemChunkTestCase(unittest.TestCase):

    root = 'root'
    path = 'path'
    id_ = hashlib.sha1('dummy_id').hexdigest()

    def setUp(self):
        fs.storage_root = tempfile.mkdtemp()
        fs.initialize()

    def tearDown(self):
        shutil.rmtree(fs.storage_root)

    def test_register_chunk(self):
        data = os.urandom(64)
        uri = '/chunked_upload'
        with app.test_request_context(uri, method='PUT', data=data):
            offset = fs.register_chunk(self.id_, request.stream)
            self.assertEqual(offset, len(data))

        test_path = os.path.join(fs.storage_root, config.chunk_storage)
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, self.id_[:2])
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, self.id_[2:])
        self.assertTrue(os.path.exists(test_path))

        with open(test_path) as f:
            self.assertEqual(f.read(), data)

    def test_remove_chunked_upload(self):
        uri = '/chunked_upload'
        chunk = os.urandom(random.randint(12, 64))
        with app.test_request_context(uri, method='PUT', data=chunk):
            fs.register_chunk(self.id_, request.stream)
        with app.test_request_context(uri, method='PUT', data=chunk):
            fs.remove_chunked_upload(self.id_)

        test_path = os.path.join(fs.storage_root, config.chunk_storage)
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, self.id_[:2])
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, self.id_[2:])
        self.assertFalse(os.path.exists(test_path))

    def test_retrieve_chunk(self):
        data = os.urandom(64)
        fs.register_chunk(self.id_, cStringIO.StringIO(data))
        with fs.retrieve_chunk_stream(self.id_) as s:
            self.assertEqual(s.read(), data)


class ChecksumCalcStreamTestCase(unittest.TestCase):

    def setUp(self):
        fs.storage_root = tempfile.mkdtemp()
        fs.initialize()

    def tearDown(self):
        shutil.rmtree(fs.storage_root)

    def test_hasher(self):
        data = os.urandom(64)
        with app.test_request_context('', method='PUT', data=data):
            s = stream.ChecksumCalcStream(request.stream)
            f_hash = fs.register_blob('root', 'f', s, s.hash)
            self.assertEqual(f_hash, hashlib.sha1(data).hexdigest())


class FilesystemStoreTestCase(unittest.TestCase):

    root = 'root'
    path = 'path'

    def setUp(self):
        fs.storage_root = tempfile.mkdtemp()
        fs.initialize()

        uri = '/files/%s/%s' % (self.root, self.path)
        self.data = os.urandom(64)
        self.ctx = app.test_request_context(uri, method='PUT', data=self.data)
        self.ctx.push()
        self.stream = stream.ChecksumCalcStream(request.stream)
        self.hash = self.stream.hash

    def tearDown(self):
        self.ctx.pop()
        shutil.rmtree(fs.storage_root)

    def test_register_blob(self):
        f_hash = fs.register_blob(self.root, self.path, self.stream, self.hash)
        self.assertEqual(len(f_hash), 40)

        test_path = fs.storage_root
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, self.root)
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, f_hash[:2])
        self.assertTrue(os.path.exists(test_path))
        test_path = os.path.join(test_path, f_hash[2:])
        self.assertTrue(os.path.exists(test_path))

        with open(test_path) as f:
            self.assertEqual(f.read(), self.data)

    def test_retrieve_blob(self):
        f_hash = fs.register_blob(self.root, self.path, self.stream, self.hash)
        with fs.retrieve_blob_stream(self.root, f_hash) as s:
            self.assertEqual(s.read(), self.data)

    def test_stat_blob(self):
        f_hash = fs.register_blob(self.root, self.path, self.stream, self.hash)
        mtime, fsize = fs.stat_blob(self.root, self.path, f_hash)
        self.assertIsNotNone(fsize)
        self.assertIsNotNone(mtime)
        self.assertEqual(fsize, len(self.data))

    def test_stat_missing_blob(self):
        self.assertEqual(fs.stat_blob(self.root, self.path, '_'), (None, None))
