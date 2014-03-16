from datetime import datetime, timedelta
import json
import mock
import random
import tools
import urllib2

from datastore.api import config, file_store


class FileTestCase(tools.FiledepotLoggedInTestCase):

    def setUp(self):
        super(FileTestCase, self).setUp()

    def tearDown(self):
        super(FileTestCase, self).tearDown()
        self.clear_store()

    def clear_store(self):
        if hasattr(file_store, 'store'):
            file_store.store.clear()


class FileGetTestCase(FileTestCase):

    def test_std(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data)
        rv = self.file.get(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)

    def test_deep(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/d3/')

        data = tools.generate_random_data()
        rv = self.file.put(tools.root, '/d1/d2/d3/f1', data)
        rv = self.file.get(tools.root, '/d1/d2/d3/f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)

    def test_deep_unexistent(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/d3/')

        rv = self.file.get(tools.root, '/d1/d2/d3/_')
        self.assertEqual(rv.status_code, 404)

    def test_deep_unexistent_dir(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/')

        rv = self.file.get(tools.root, '/d1/d2/d3/_')
        self.assertEqual(rv.status_code, 404)

    def test_mid_data(self):
        data = tools.generate_random_data(4096)
        rv = self.file.put(tools.root, 'f1', data)
        rv = self.file.get(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)

    def test_bad_path(self):
        rv = self.file.get(tools.root, '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.get(tools.root, '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.get(tools.root, '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

    def test_big_data(self):
        data = tools.generate_random_data(1024 * 1024)
        rv = self.file.put(tools.root, 'f1', data)
        rv = self.file.get(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)

    def test_corrupted(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data)
        self.clear_store()
        rv = self.file.get(tools.root, 'f1')
        self.assertEqual(rv.status_code, 404)

    def test_embedded_metadata(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data)
        rv = self.file.get(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)
        json_data = json.loads(rv.headers['x-datastore-metadata'])
        self.assertValidFileMetadata(json_data, tools.root, '/f1', data)


class FileMetadataTestCase(FileTestCase):

    def test_hash(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        options = {'hash': rv.json['hash']}
        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 304)

    def test_hash_change_file(self):
        data = tools.generate_random_data()
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)
        options = {'hash': rv.json['hash']}

        rv = self.file.put(tools.root, '/d1/f1', data + '_')
        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

    def test_hash_delete_dir(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.fileops.create_folder(tools.root, 'd1/d2')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)
        options = {'hash': rv.json['hash']}
        rv = self.fileops.delete(tools.root, '/d1/d2')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

    def test_hash_delete_file(self):
        data = tools.generate_random_data()
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)
        options = {'hash': rv.json['hash']}
        rv = self.fileops.delete(tools.root, '/d1/f1')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

    def test_hash_metadata_param(self):
        data = tools.generate_random_data()
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)
        options = {'hash': rv.json['hash']}

        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 304)
        options.update(include_deleted=True)
        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 304)

    def test_hash_put_file(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        options = {'hash': rv.json['hash']}
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

    def test_hash_change_subdir(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.fileops.create_folder(tools.root, 'd1/d2')
        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        options = {'hash': rv.json['hash']}
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'd1/d2/f1', data)
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, 'd1', **options)
        self.assertEqual(rv.status_code, 304)

    def test_bad_param(self):
        rv = self.file.metadata(tools.root, '', list='_')
        self.assertEqual(rv.status_code, 400)

        rv = self.file.metadata(tools.root, '', include_deleted='_')
        self.assertEqual(rv.status_code, 400)

    def test_bad_path(self):
        rv = self.file.metadata(tools.root, '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.metadata(tools.root, '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.metadata(tools.root, '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

    def test_mimetype(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1.pdf', data)
        rv = self.file.metadata(tools.root, 'f1.pdf')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.json['mime_type'], 'application/pdf')
        self.assertValidFileMetadata(rv.json, tools.root, '/f1.pdf', data)

    def test_root(self):
        rv = self.file.metadata(tools.root, '')
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/')

    def test_folder(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.metadata(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.json['contents'], [])
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

    def test_listing(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', '')

        rv = self.file.metadata(tools.root, '/d1/')
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

        content = rv.json.get('contents')
        self.assertEqual(len(content), 1)
        self.assertValidFileMetadata(content[0], tools.root, '/d1/f1', '')

    def test_listing_off(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', '')

        rv = self.file.metadata(tools.root, '/d1/', list='false')
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn('contents', rv.json)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

    def test_exclude_deleted(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', '')
        rv = self.fileops.delete(tools.root, '/d1/f1')

        rv = self.file.metadata(tools.root, '/d1/')
        self.assertEqual(rv.status_code, 200)
        self.assertFalse(rv.json['contents'], [])

    def test_bad_root(self):
        rv = self.file.metadata('dummy', '')
        self.assertEqual(rv.status_code, 403)

    def test_missing(self):
        rv = self.file.metadata(tools.root, 'f')
        self.assertEqual(rv.status_code, 404)

    def test_include_deleted(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        rv = self.file.put(tools.root, '/d1/f1', '')
        rv = self.fileops.delete(tools.root, '/d1/f1')

        options = {'include_deleted': 'true'}
        rv = self.file.metadata(tools.root, '/d1/', **options)
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

        content = rv.json.get('contents')
        self.assertEqual(len(content), 1)
        self.assertTrue(content[0]['is_deleted'])
        self.assertValidFileMetadata(content[0], tools.root, '/d1/f1', '')

    def test_hierarchy(self):
        rv = self.fileops.create_folder(tools.root, '/d1')
        rv = self.fileops.create_folder(tools.root, '/d1/d2')
        rv = self.fileops.create_folder(tools.root, '/d1/d2/d3')
        rv = self.file.put(tools.root, '/d1/f1', 'f1')
        rv = self.file.put(tools.root, '/d1/f2', 'f2')
        rv = self.file.put(tools.root, '/d1/d2/f3', 'f3')

        rv = self.file.metadata(tools.root, '/d1/')
        self.assertEqual(rv.status_code, 200)
        self.assertValidDirMetadata(rv.json, tools.root, '/d1')

        content = rv.json.get('contents')
        self.assertEqual(len(content), 3)
        self.assertValidDirMetadata(content[0], tools.root, '/d1/d2')
        self.assertValidFileMetadata(content[1], tools.root, '/d1/f1', 'f1')
        self.assertValidFileMetadata(content[2], tools.root, '/d1/f2', 'f2')

    def test_from_key(self):
        rv = self.file.put(tools.root, 'f1', 'f1')
        rv = self.file.shares(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)

        json_data = rv.json
        rv = self.file.metadata(key=json_data['key'])
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', 'f1')
        rv = self.file.app.get(json_data['metadata'])
        self.assertEqual(rv.status_code, 200)
        json_data = json.loads(rv.data)
        self.assertValidFileMetadata(json_data, tools.root, '/f1', 'f1')

    def test_include_links(self):
        rv = self.file.put(tools.root, 'f1', 'f1')
        rv = self.file.shares(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.metadata(tools.root, '', include_links=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('link', rv.json['contents'][0])


class FilePutTestCase(FileTestCase):

    def test_std(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data)

    def test_dup_content(self):
        data = tools.generate_random_data()

        rv = self.file.put(tools.root, 'f1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data)

        rv = self.file.put(tools.root, 'f1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data)

    def test_dup_filepath(self):
        data1 = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data1)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data1)

        data2 = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data2)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data2)

    def test_subdir(self):
        rv = self.fileops.create_folder(tools.root, '/d1/')
        self.assertEqual(rv.status_code, 200)

        data = tools.generate_random_data()
        rv = self.file.put(tools.root, '/d1/f1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/d1/f1', data)

    def test_bad_path(self):
        rv = self.file.put(tools.root, '.', '_')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.put(tools.root, '/d1/./f1', '_')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.put(tools.root, '/d1/../f1', '_')
        self.assertEqual(rv.status_code, 403)

    def test_mid_data(self):
        data = tools.generate_random_data(4096)
        rv = self.file.put(tools.root, 'f1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data)

    def test_big_data(self):
        data = tools.generate_random_data(1024 * 1024)
        rv = self.file.put(tools.root, 'f1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', data)

    def test_null_content(self):
        rv = self.file.put(tools.root, 'f1', None)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1', None)

    def test_unexistent_dir(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, '/d1/d2/f1', data)
        self.assertEqual(rv.status_code, 404)

    def test_overwrite_deleted_dir(self):
        rv = self.fileops.create_folder(tools.root, '/d1/')
        rv = self.fileops.delete(tools.root, '/d1/')
        self.assertEqual(rv.status_code, 200)

        data = tools.generate_random_data()
        rv = self.file.put(tools.root, '/d1', data)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/d1', data)

    def test_new_root(self):
        rv = self.file.put('dummy', 'f1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 403)

    def test_conflict_with_overwrite(self):
        data = [tools.generate_random_data() for _ in range(2)]
        rv = self.file.put(tools.root, '/f1.txt', data[0])
        rv = self.file.put(tools.root, '/f1.txt', data[1], overwrite=True)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1.txt', data[1])

    def test_conflict_without_overwrite(self):
        data = [tools.generate_random_data() for _ in range(3)]
        rv = self.file.put(tools.root, '/f1.txt', data[0])
        rv = self.file.put(tools.root, '/f1.txt', data[1], overwrite=False)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1 (1).txt',
                                     data[1])
        rv = self.file.put(tools.root, '/f1.txt', data[2], overwrite=False)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1 (2).txt',
                                     data[2])

    def test_conflict_good_parent_rev(self):
        data = [tools.generate_random_data() for _ in range(2)]
        rv = self.file.put(tools.root, '/f1.txt', data[0])
        self.assertEqual(rv.status_code, 200)
        rev = rv.json['rev']

        rv = self.file.put(tools.root, '/f1.txt', data[1], parent_rev=rev)
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root, '/f1.txt', data[1])

    def test_conflict_unknown_parent_rev(self):
        data = [tools.generate_random_data() for _ in range(2)]
        rv = self.file.put(tools.root, '/f1.txt', data[0])
        rv = self.file.put(tools.root, '/f1.txt', data[1], parent_rev='_')
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root,
                                     '/f1 (conflicted copy).txt', data[1])

    def test_conflict_with_conflicted_copy(self):
        data = [tools.generate_random_data() for _ in range(4)]
        rv = self.file.put(tools.root, '/f1.txt', data[0])
        rv = self.file.put(tools.root, '/f1.txt', data[1], parent_rev='_')
        rv = self.file.put(tools.root, '/f1.txt', data[2], overwrite=False,
                           parent_rev='_')
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root,
                                     '/f1 (conflicted copy) (1).txt', data[2])
        rv = self.file.put(tools.root, '/f1.txt', data[3], overwrite=True,
                           parent_rev='_')
        self.assertEqual(rv.status_code, 200)
        self.assertValidFileMetadata(rv.json, tools.root,
                                     '/f1 (conflicted copy) (2).txt', data[3])

    def test_put_resets_deleted(self):
        data = [tools.generate_random_data() for _ in range(4)]
        rv = self.file.put(tools.root, '/f1.txt', data[0])
        self.assertEqual(rv.status_code, 200)

        rv = self.fileops.delete(tools.root, '/f1.txt')
        self.assertEqual(rv.status_code, 200)
        self.assertDictContainsSubset({'is_deleted': True}, rv.json)

        rv = self.file.put(tools.root, '/f1.txt', data[0])
        self.assertEqual(rv.status_code, 200)
        self.assertFalse(rv.json.get('is_deleted', False))

    def test_put_with_same_name_directory(self):
        rv = self.fileops.create_folder(tools.root, 'test')
        self.assertEqual(rv.status_code, 200)
        rv = self.file.put(tools.root, 'test', tools.generate_random_data())
        self.assertEqual(rv.status_code, 403)


class FileRevisionsTestCase(FileTestCase):

    def test_bad_path(self):
        rv = self.file.revisions(tools.root, '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.revisions(tools.root, '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.revisions(tools.root, '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

    def test_default_limit(self):
        for i in xrange(15):
            rv = self.file.put(tools.root, '/f1', str(i))

        rv = self.file.revisions(tools.root, '/f1')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(rv.json), 10)

    def test_depth(self):
        count = random.randint(10, 20)
        for i in xrange(count):
            rv = self.file.put(tools.root, '/f1', str(i))

        rv = self.file.revisions(tools.root, '/f1', rev_limit=100)
        self.assertEqual(rv.status_code, 200)

        self.assertEqual(len(rv.json), count)
        for i, item in enumerate(reversed(rv.json)):
            self.assertValidFileMetadata(item, tools.root, '/f1', str(i))

    def test_dir(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.revisions(tools.root, 'd1')
        self.assertEqual(rv.status_code, 404)

    def test_limit(self):
        rv = self.file.put(tools.root, 'f1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.file.revisions(tools.root, 'f1', rev_limit=0)
        self.assertEqual(rv.status_code, 406)
        rv = self.file.revisions(tools.root, 'f1', rev_limit=1)
        self.assertEqual(rv.status_code, 200)
        rv = self.file.revisions(tools.root, 'f1', rev_limit=1000)
        self.assertEqual(rv.status_code, 200)
        rv = self.file.revisions(tools.root, 'f1', rev_limit=1001)
        self.assertEqual(rv.status_code, 406)

    def test_std(self):
        rv = self.file.put(tools.root, 'f1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.file.revisions(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)

    def test_missing(self):
        rv = self.file.revisions(tools.root, 'f1')
        self.assertEqual(rv.status_code, 404)


class FileLinkTestCase(FileTestCase):

    def test_bad_path(self):
        rv = self.file.shares(tools.root, '.')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.shares(tools.root, '/d1/./f1')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.shares(tools.root, '/d1/../f1')
        self.assertEqual(rv.status_code, 403)

    def test_create(self):
        rv = self.file.put(tools.root, 'f1', tools.generate_random_data())
        self.assertEqual(rv.status_code, 200)

        rv = self.file.shares(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('link', rv.json)
        self.assertIn('expires', rv.json)

    def test_create_bad_object(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.shares(tools.root, 'd1')
        self.assertEqual(rv.status_code, 404)

    def test_delete_bad_link(self):
        rv = self.file.remove_shares('dummy')
        self.assertEqual(rv.status_code, 404)

    def test_delete_link(self):
        rv = self.file.put(tools.root, 'f1', tools.generate_random_data())
        rv = self.file.shares(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)

        key = rv.json['key']
        rv = self.file.remove_shares(key)
        self.assertEqual(rv.status_code, 200)

        rv = self.file.get(key)
        self.assertEqual(rv.status_code, 404)

    def test_missing_file(self):
        rv = self.file.shares(tools.root, '_')
        self.assertEqual(rv.status_code, 404)

    def test_override_expire(self):
        rv = self.file.put(tools.root, 'f1', tools.generate_random_data())
        rv = self.file.shares(tools.root, 'f1', expire_days=3)
        self.assertEqual(rv.status_code, 200)
        link = urllib2.quote(rv.json['link'])

        old_date = datetime.utcnow() + timedelta(days=3, seconds=-1)
        with mock.patch('datastore.api.files.shares.datetime') as m:
            m.utcnow.return_value = old_date
            rv = self.file.app.get(link)
            self.assertEqual(rv.status_code, 200)

        old_date = datetime.utcnow() + timedelta(days=3, seconds=+1)
        with mock.patch('datastore.api.files.shares.datetime') as m:
            m.utcnow.return_value = old_date
            rv = self.file.app.get(link)
            self.assertEqual(rv.status_code, 404)

    def test_override_expire_values(self):
        rv = self.file.put(tools.root, 'f1', tools.generate_random_data())
        rv = self.file.shares(tools.root, 'f1', expire_days=0)
        self.assertEqual(rv.status_code, 406)
        rv = self.file.shares(tools.root, 'f1', expire_days=1)
        self.assertEqual(rv.status_code, 200)
        rv = self.file.shares(tools.root, 'f1', expire_days=10000)
        self.assertEqual(rv.status_code, 200)
        rv = self.file.shares(tools.root, 'f1', expire_days=10001)
        self.assertEqual(rv.status_code, 406)

    def test_get_bad_link(self):
        rv = self.file.app.get('/files/dummy')
        self.assertEqual(rv.status_code, 404)

    def test_get_expired_link(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data)
        rv = self.file.shares(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)

        old_date = datetime.utcnow() + timedelta(days=1, seconds=1)
        with mock.patch('datastore.api.files.shares.datetime') as m:
            m.utcnow.return_value = old_date
            rv = self.file.app.get(urllib2.quote(rv.json['link']))
            self.assertEqual(rv.status_code, 404)

    def test_get_link(self):
        data = tools.generate_random_data()
        rv = self.file.put(tools.root, 'f1', data)
        rv = self.file.shares(tools.root, 'f1')
        self.assertEqual(rv.status_code, 200)
        json_data = rv.json

        rv = self.file.app.get(json_data['link'])
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, data)


class SearchTestCase(FileTestCase):

    def setUp(self):
        super(FileTestCase, self).setUp()
        self.fileops.create_folder(tools.root, 'foo1')
        self.fileops.create_folder(tools.root, 'foo1/bar2')
        self.fileops.create_folder(tools.root, 'plop3')
        self.file.put(tools.root, 'foo1/animals', 'animals')
        self.file.put(tools.root, 'foo1/bar2/dark_side', 'dark_side')
        self.file.put(tools.root, 'plop3/meddle', 'meddle')
        self.file.put(tools.root, 'plop3/dark', 'dark')

    def test_bad_path(self):
        rv = self.file.search(tools.root, '.', query='abc')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.search(tools.root, '/d1/./f1', query='abc')
        self.assertEqual(rv.status_code, 403)
        rv = self.file.search(tools.root, '/d1/../f1', query='abc')
        self.assertEqual(rv.status_code, 403)

    def test_limit(self):
        rv = self.fileops.create_folder(tools.root, 'd1')
        self.assertEqual(rv.status_code, 200)

        rv = self.file.search(tools.root, 'd1', query='abc', file_limit=0)
        self.assertEqual(rv.status_code, 406)
        rv = self.file.search(tools.root, 'd1', query='abc', file_limit=1)
        self.assertEqual(rv.status_code, 200)
        rv = self.file.search(tools.root, 'd1', query='abc', file_limit=1000)
        self.assertEqual(rv.status_code, 200)
        rv = self.file.search(tools.root, 'd1', query='abc', file_limit=1001)
        self.assertEqual(rv.status_code, 406)

    def test_query_minimum(self):
        rv = self.file.search(tools.root, '', query='a')
        self.assertEqual(rv.status_code, 400)

    def test_query_match_1(self):
        rv = self.file.search(tools.root, '', query='foo')
        self.assertEqual(len(rv.json), 1)
        self.assertValidDirMetadata(rv.json[0], tools.root, '/foo1')

    def test_query_match_2(self):
        rv = self.file.search(tools.root, '', query='dark')
        self.assertEqual(len(rv.json), 2)
        self.assertValidFileMetadata(rv.json[0], tools.root,
                                     '/foo1/bar2/dark_side', 'dark_side')
        self.assertValidFileMetadata(rv.json[1], tools.root,
                                     '/plop3/dark', 'dark')

    def test_query_subdir(self):
        rv = self.file.search(tools.root, 'foo1/bar2/', query='dark')
        self.assertEqual(len(rv.json), 1)
        self.assertValidFileMetadata(rv.json[0], tools.root,
                                     '/foo1/bar2/dark_side', 'dark_side')

    def test_query_unmatched(self):
        rv = self.file.search(tools.root, '', query='atom_heart')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.json, [])

    def test_search_bad_root(self):
        rv = self.file.search(tools.root, 'foo1/animals', query='___')
        self.assertEqual(rv.status_code, 404)

    def test_search_missing_root(self):
        rv = self.file.search(tools.root, 'd1', query='___')
        self.assertEqual(rv.status_code, 404)
