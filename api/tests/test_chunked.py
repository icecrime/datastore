from datetime import datetime, timedelta
import mock

from datastore.api import file_store

import tools


class ChunkedUploadTestCase(tools.FiledepotLoggedInTestCase):

    def clear_store(self):
        if hasattr(file_store, 'store'):
            file_store.store.clear()

    def tearDown(self):
        super(tools.FiledepotLoggedInTestCase, self).tearDown()
        self.clear_store()

    def assertValidChunkResponse(self, data, offset=None, upload_id=None):
        self.assertIn('expires', data)
        self.assertIn('offset', data)
        self.assertIn('upload_id', data)
        if offset is not None:
            self.assertEqual(data['offset'], offset)
        if upload_id is not None:
            self.assertEqual(data['upload_id'], upload_id)

    def test_bad_offset(self):
        rv = self.file.chunked_upload('_')
        self.assertEqual(rv.status_code, 200)

        id_ = rv.json['upload_id']
        rv = self.file.chunked_upload('_', offset=0, upload_id=id_)
        self.assertEqual(rv.status_code, 400)
        self.assertValidChunkResponse(rv.json, 1, id_)

    def test_bad_upload_id(self):
        rv = self.file.chunked_upload('_', upload_id='dummy')
        self.assertEqual(rv.status_code, 404)

    def test_commit_bad_upload_id(self):
        rv = self.file.commit_chunked_upload(tools.root, '_', upload_id='_')
        self.assertEqual(rv.status_code, 400)

    def test_create_with_offset(self):
        rv = self.file.chunked_upload('_', offset=1)
        self.assertEqual(rv.status_code, 400)

    def test_expires(self):
        rv = self.file.chunked_upload('_')
        self.assertEqual(rv.status_code, 200)

        old_date = datetime.utcnow() + timedelta(days=1, seconds=1)
        mock_element = 'datastore.api.files.chunked_upload.datetime'
        with mock.patch(mock_element) as mock_datetime:
            mock_datetime.datetime.utcnow.return_value = old_date
            id_ = rv.json['upload_id']
            rv = self.file.chunked_upload('_', offset=0, upload_id=id_)
            self.assertEqual(rv.status_code, 404)

    def test_std(self):
        data = [tools.generate_random_data() for _ in range(5)]

        rv = self.file.chunked_upload(data[0])
        self.assertEqual(rv.status_code, 200)
        self.assertValidChunkResponse(rv.json, offset=len(data[0]))

        id_ = rv.json['upload_id']
        for chunk in data[1:]:
            offset = rv.json['offset']
            rv = self.file.chunked_upload(chunk, offset=offset, upload_id=id_)
            self.assertEqual(rv.status_code, 200)
            self.assertValidChunkResponse(rv.json, upload_id=id_,
                                          offset=offset + len(chunk))

        rv = self.file.commit_chunked_upload(tools.root, '/f1', upload_id=id_)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', ''.join(data))
