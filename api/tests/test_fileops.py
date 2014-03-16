import tools


class FileopsCreateFolderTestCase(tools.FiledepotLoggedInTestCase):

    def test_bad_path(self):
        rv = self.fileops.create_folder(tools.root, '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.create_folder(tools.root, '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.create_folder(tools.root, '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

    def test_std(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)

        self.assertIn('rev', rv.json)
        self.assertIn('modified', rv.json)
        self.assertNotIn('is_deleted', rv.json)
        self.assertDictContainsSubset({
            'is_dir': True,
            'path': '/d1',
            'root': tools.root,
            'size': '0.0 bytes',
        }, rv.json)

    def test_nested(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/')
        self.assertEqual(rv.status_code, 200)

        self.assertIn('rev', rv.json)
        self.assertIn('modified', rv.json)
        self.assertNotIn('is_deleted', rv.json)
        self.assertDictContainsSubset({
            'is_dir': True,
            'path': '/d1/d2',
            'root': tools.root,
            'size': '0.0 bytes',
        }, rv.json)

    def test_empty_path(self):
        rv = self.fileops.create_folder(tools.root, '')
        self.assertEqual(rv.status_code, 403)

    def test_bad_root(self):
        rv = self.fileops.create_folder('_', '/d1')
        self.assertEqual(rv.status_code, 403)

    def test_incomplete_path(self):
        rv = self.fileops.create_folder(tools.root, '/d1/d2/')
        self.assertEqual(rv.status_code, 404)

    def test_dup_folder(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1')
        self.assertEqual(rv.status_code, 403)

    def test_recreate_deleted(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.delete(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.create_folder(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.json.get('is_deleted', False), False)

    def test_create_same_name_file(self):
        rv = self.file.put(tools.root, 'd1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.create_folder(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)


class FileopsCopyTestCase(tools.FiledepotLoggedInTestCase):

    def test_bad_copy(self):
        rv = self.fileops.copy(tools.root, '/d1/f1', '')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.copy(tools.root, '', '/d2/f2')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.copy('', '/d1/f1', '/d2/f2')
        self.assertEqual(rv.status_code, 403)

    def test_bad_path(self):
        rv = self.fileops.copy(tools.root, 'source', '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.copy(tools.root, 'source', '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.copy(tools.root, 'source', '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

        rv = self.fileops.copy(tools.root, '.', 'destination')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.copy(tools.root, '/d1/./f1', 'destination')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.copy(tools.root, '/d1/../f1', 'destination')
        self.assertEqual(rv.status_code, 403)

    def test_copy_conflict_dir(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d2/')
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1', '/d2/')
        self.assertEqual(rv.status_code, 403)

    def test_copy_conflict_file(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d2/')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.file.put(tools.root, '/d2/f2', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1/f1', '/d2/f2')
        self.assertEqual(rv.status_code, 403)

    def test_copy_as_subfile(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.file.put(tools.root, '/d1/f2', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1/f1', '/d1/f2/f2')
        self.assertEqual(rv.status_code, 403)

    def test_copy_overwrite_dir(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d2')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1/f1', '/d2/')
        self.assertEqual(rv.status_code, 200)

    def test_copy_superset(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/')
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1/d2/', '/d1/d2/d3/')
        self.assertEqual(rv.status_code, 403)

    def test_deleted_file(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.fileops.delete(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1/f1', '/d1/f2')
        self.assertEqual(rv.status_code, 404)

    def test_copy_to_deleted_file(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.file.put(tools.root, '/d1/f2', tools.generate_random_data())
        rv = self.fileops.delete(tools.root, '/d1/f2')
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.copy(tools.root, '/d1/f1', '/d1/f2')
        self.assertEqual(rv.status_code, 200)

    def test_dir_with_content(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.file.put(tools.root, '/d1/f2', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)
        src_metadata = rv.json

        rv = self.fileops.copy(tools.root, '/d1', '/d2/')
        self.assertEqual(rv.status_code, 200)
        dst_metadata = rv.json

        # Can't compare tree revisions: they change with the instance
        src_metadata.pop('rev')
        dst_metadata.pop('rev')

        self.assertEqual(src_metadata.pop('path'), '/d1')
        self.assertEqual(src_metadata['contents'][0].pop('path'), '/d1/f1')
        self.assertEqual(src_metadata['contents'][1].pop('path'), '/d1/f2')
        self.assertEqual(dst_metadata.pop('path'), '/d2')
        self.assertEqual(dst_metadata['contents'][0].pop('path'), '/d2/f1')
        self.assertEqual(dst_metadata['contents'][1].pop('path'), '/d2/f2')
        self.assertDictEqual(src_metadata, dst_metadata)

    def test_missing(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)
        rv = self.fileops.copy(tools.root, '/d1/f1', '/d1/f2')
        self.assertEqual(rv.status_code, 404)

    def test_missing_in_missing_dir(self):
        rv = self.fileops.copy(tools.root, '/d1/f1', '/d1/f2')
        self.assertEqual(rv.status_code, 403)

    def test_simple_dir(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)
        src_metadata = rv.json

        rv = self.fileops.copy(tools.root, '/d1', '/d2/')
        self.assertEqual(rv.status_code, 200)
        dst_metadata = rv.json

        # Can't compare tree revisions: they change with the instance
        src_metadata.pop('rev')
        dst_metadata.pop('rev')

        self.assertEqual(src_metadata.pop('path'), '/d1')
        self.assertEqual(dst_metadata.pop('path'), '/d2')
        self.assertDictEqual(src_metadata, dst_metadata)

        # Verify through /metadata that the folder does contain both files.
        rv = self.file.metadata(tools.root, '')
        dir_metadata = rv.json
        sub_elements = [c['path'] for c in dir_metadata['contents']]
        self.assertIn('/d1', sub_elements)
        self.assertIn('/d1', sub_elements)

    def test_simple_file(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)
        src_metadata = rv.json

        rv = self.fileops.copy(tools.root, '/d1/f1', '/d1/f2')
        self.assertEqual(rv.status_code, 200)
        dst_metadata = rv.json

        self.assertEqual(src_metadata.pop('path'), '/d1/f1')
        self.assertEqual(dst_metadata.pop('path'), '/d1/f2')
        self.assertDictEqual(src_metadata, dst_metadata)

        # Verify through /metadata that the folder does contain both files.
        rv = self.file.metadata(tools.root, 'd1')
        dir_metadata = rv.json
        sub_elements = [c['path'] for c in dir_metadata['contents']]
        self.assertIn('/d1/f1', sub_elements)
        self.assertIn('/d1/f2', sub_elements)


class FileopsDeleteTestCase(tools.FiledepotLoggedInTestCase):

    def test_bad_root(self):
        rv = self.fileops.delete('', '/d1/f1')
        self.assertEqual(rv.status_code, 403)

    def test_delete_twice(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.fileops.delete(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 200)
        rv = self.fileops.delete(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 404)

    def test_file__std(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.fileops.delete(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 200)

        self.assertIn('rev', rv.json)
        self.assertIn('modified', rv.json)
        self.assertDictContainsSubset({
            'is_deleted': True,
            'path': '/d1/f1',
            'root': tools.root,
        }, rv.json)

    def test_folder__std(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.delete(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)

        self.assertIn('rev', rv.json)
        self.assertIn('modified', rv.json)
        self.assertDictContainsSubset({
            'is_deleted': True,
            'is_dir': True,
            'path': '/d1',
            'root': tools.root,
            'size': '0.0 bytes',
        }, rv.json)

    def test_none(self):
        rv = self.fileops.delete(None, None)
        self.assertEqual(rv.status_code, 400)

    def test_recursive_folder(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2')
        rv = self.file.put(tools.root, '/d1/f1', tools.generate_random_data())
        rv = self.fileops.delete(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)

        for item in ['/d1', '/d1/d2', '/d1/f1']:
            rv = self.file.metadata(tools.root, item)
            self.assertTrue(rv.json['is_deleted'])

    def test_unexistant(self):
        rv = self.fileops.delete(tools.root, '_')
        self.assertEqual(rv.status_code, 404)


class FileopsMoveTestCase(tools.FiledepotLoggedInTestCase):

    def test_bad_move(self):
        rv = self.fileops.move(tools.root, '/d1/f1', '')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.move(tools.root, '', '/d2/f2')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.move('', '/d1/f1', '/d2/f2')
        self.assertEqual(rv.status_code, 403)

    def test_bad_path(self):
        rv = self.fileops.move(tools.root, 'source', '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.move(tools.root, 'source', '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.move(tools.root, 'source', '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

        rv = self.fileops.move(tools.root, '.', 'destination')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.move(tools.root, '/d1/./f1', 'destination')
        self.assertEqual(rv.status_code, 403)
        rv = self.fileops.move(tools.root, '/d1/../f1', 'destination')
        self.assertEqual(rv.status_code, 403)

    def test_simple_dir(self):
        data = tools.generate_random_data()

        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.move(tools.root, '/d1', '/d2')
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d2')

        rv = self.file.metadata(tools.root, '/d1')
        self.assertEqual(rv.status_code, 200)
        self.assertDictContainsSubset({'is_deleted': True}, rv.json)

        rv = self.file.metadata(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 200)
        self.assertDictContainsSubset({'is_deleted': True}, rv.json)

        rv = self.file.get(tools.root, '/d2/f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)

    def test_simple_file(self):
        data = tools.generate_random_data()

        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d2')
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.move(tools.root, '/d1/f1', '/d2/f2')
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/d2/f2', data)

        rv = self.file.metadata(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 200)
        self.assertDictContainsSubset({'is_deleted': True}, rv.json)

        rv = self.file.get(tools.root, '/d2/f2')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)
