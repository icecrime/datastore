import functools
import hashlib
import json
import os
import random
from . import unittest

import datastore.api
from datastore.api.helpers import display


root = 'sandbox'


def _post_json(app, uri, data):
    return app.post(
        uri,
        data=json.dumps(data),
        content_type='application/json'
    )


def with_json_data(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        rv = fn(*args, **kwargs)
        if rv.data and rv.headers.get('content-type') == 'application/json':
            rv.json = json.loads(rv.data)
        return rv
    return wrapper


def generate_random_data(length=None):
    data_length = (4, 8)
    return os.urandom(length or random.randint(*data_length))


class User(object):

    def __init__(self, app):
        self.app = app

    def create(self, data):
        return self.app.post('/users', data=data)

    @with_json_data
    def info(self):
        return self.app.get('/account/info')

    @with_json_data
    def login(self, data):
        return self.app.post('/login', data=data)

    def logout(self):
        return self.app.get('/logout')

    @with_json_data
    def update(self, data):
        return self.app.post('/account/info', data=data)


class File(object):

    def __init__(self, app):
        self.app = app

    @with_json_data
    def chunked_upload(self, data, **kwargs):
        uri = '/chunked_upload'
        return self.app.put(uri, data=data, query_string=kwargs)

    @with_json_data
    def commit_chunked_upload(self, root, path, **kwargs):
        uri = '/'.join(['/commit_chunked_upload', root, path.lstrip('/')])
        return self.app.post(uri, data=kwargs)

    def get(self, root, path=''):
        uri = '/'.join(['/files', root, path.lstrip('/')])
        return self.app.get(uri)

    @with_json_data
    def metadata(self, root=None, path=None, **kwargs):
        uri = '/metadata'
        if root is not None:
            uri = '/'.join([uri, root, path.lstrip('/')])
        return self.app.get(uri, query_string=kwargs)

    @with_json_data
    def put(self, root, path, data, **kwargs):
        uri = '/'.join(['/files', root, path.lstrip('/')])
        return self.app.put(uri, data=data, query_string=kwargs)

    @with_json_data
    def remove_shares(self, key):
        uri = '/'.join(['/shares', key])
        return self.app.delete(uri)

    @with_json_data
    def revisions(self, root, path, **kwargs):
        uri = '/'.join(['/revisions', root, path.lstrip('/')])
        return self.app.get(uri, query_string=kwargs)

    @with_json_data
    def search(self, root, path, **kwargs):
        uri = '/'.join(['/search', root, path.lstrip('/')])
        return self.app.get(uri, query_string=kwargs)

    @with_json_data
    def shares(self, root, path, **kwargs):
        uri = '/'.join(['/shares', root, path.lstrip('/')])
        return self.app.post(uri, query_string=kwargs)


class Fileop(object):

    def __init__(self, app):
        self.app = app

    @with_json_data
    def copy(self, root, from_path, to_path):
        data = {'root': root, 'from_path': from_path, 'to_path': to_path}
        return self.app.post('/fileops/copy', data=data)

    @with_json_data
    def create_folder(self, root, path):
        data = {'root': root, 'path': path}
        return self.app.post('/fileops/create_folder', data=data)

    @with_json_data
    def delete(self, root, path):
        data = {'root': root, 'path': path}
        return self.app.post('/fileops/delete', data=data)

    @with_json_data
    def move(self, root, from_path, to_path):
        data = {'root': root, 'from_path': from_path, 'to_path': to_path}
        return self.app.post('/fileops/move', data=data)


class FiledepotTestCase(unittest.TestCase):

    def assertValidMetadata(self, data, root, path):
        self.assertIn('rev', data)
        self.assertIn('modified', data)
        self.assertDictContainsSubset({
            'path': path,
            'root': root,
        }, data)

    def assertValidDirMetadata(self, data, root, path):
        self.assertValidMetadata(data, root, path)
        self.assertDictContainsSubset({
            'bytes': 0,
            'is_dir': True,
            'size': '0.0 bytes',
        }, data)

    def assertValidFileMetadata(self, data, root, path, content=None):
        self.assertValidMetadata(data, root, path)

        # Size field is a human readable format: tedious to test without
        # relying on the same serialization function that was used to produce
        # the string in the first place.
        content_length = len(content) if content else 0
        self.assertDictContainsSubset({
            'bytes': content_length,
            'is_dir': False,
            'size': display.human_size(content_length),
        }, data)

        # Revision corresponds to the file hash, and we want to detect that we
        # never send the empty string's SHA1 hash (unless the content is really
        # empty, obviously).
        if content_length:
            rev = data['rev']
            self.assertNotEqual(rev, hashlib.sha1().hexdigest()[:len(rev)],
                                'Default SHA1 returned for a non-empty file')

    def setUp(self):
        # Reset the database engine
        datastore.api.create_session_factory()

        app = datastore.api.app.test_client()

        self.file = File(app)
        self.fileops = Fileop(app)
        self.user = User(app)

    def tearDown(self):
        try:
            os.unlink(datastore.api.config.database['database'])
        except OSError:
            pass


class FiledepotLoggedInTestCase(FiledepotTestCase):

    user_data = {'email': 'e', 'password': 'p' * 32}

    def setUp(self):
        super(FiledepotLoggedInTestCase, self).setUp()
        self.user.create(self.user_data)
        self.user.login(self.user_data)

    def tearDown(self):
        self.user.logout()
        super(FiledepotLoggedInTestCase, self).tearDown()
