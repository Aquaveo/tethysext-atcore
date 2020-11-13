import os
import shutil
from unittest import mock
import uuid

from tethysext.atcore.exceptions import FileDatabaseNotFoundError, FileCollectionNotFoundError, UnboundFileDatabaseError
from tethysext.atcore.models.file_database import FileCollection, FileCollectionClient, FileDatabase, FileDatabaseClient
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FileDatabaseClientTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         'files', 'file_database_client_tests')
        )

    def get_database_instance(self, database_id, root_directory, database_meta=None):
        """
        A helper function to generate a FileDatabase in the database.

        Args:
            database_id (uuid.UUID): a UUID to assign the id for the FileDatabase object
            root_directory (str): root directory for a FileDatabase
            database_meta (dict): A dictionary of meta for the FileDatabase object
        """
        if database_meta is None:
            database_meta = {}

        database_instance = FileDatabase(
            id=database_id,  # We need to set the id here for the test path.
            root_directory=root_directory,
            meta=database_meta,
        )

        self.session.add(database_instance)
        self.session.commit()

        return database_instance

    def get_collection_instance(self, collection_id, database_id, collection_meta):

        collection_instance = FileCollection(
            id=collection_id,
            file_database_id=database_id,
            meta=collection_meta,
        )

        self.session.add(collection_instance)
        self.session.commit()

        return collection_instance

    def test_new_file_database_client(self):
        """Test the new function on the file database client."""
        self.assertTrue(self.session.query(FileDatabase).count() == 0)
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_file_database_client')
        database_client = FileDatabaseClient.new(self.session, root_dir)
        self.assertTrue(self.session.query(FileDatabase).count() == 1)
        self.assertTrue(os.path.exists(database_client.path))
        self.assertTrue(os.path.exists(database_client.path))

    def test_existing_file_database_client(self):
        """Test Generating a FileDatabaseClient from and existing FileDatabase."""
        database_id = uuid.UUID('{4b62335d-5b43-4e3b-bba7-07cd88cc2205}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_file_database_client')
        database_instance = self.get_database_instance(database_id, root_dir, {'TestKey': 'TestVal'})
        database_client = FileDatabaseClient(self.session, database_instance.id)
        self.assertEqual(database_client.path, os.path.join(root_dir, str(database_id)))

    def test_path_property(self):
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_path_property')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir, database_meta={},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        expected_path = os.path.abspath(os.path.join(root_dir, str(database_id)))
        self.assertEqual(database_client.path, expected_path)

    def test_setting_localized_path(self):
        """Test the setting a localized root directory."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_path_property')
        database_instance = self.get_database_instance(
            database_id=database_id,  root_directory=root_dir, database_meta={}
        )

        new_localized_path = os.path.abspath(os.path.join(root_dir, 'new_localized_directory'))
        expected_path = os.path.abspath(os.path.join(new_localized_path, str(database_instance.id)))

        database_client = FileDatabaseClient(self.session, database_id)

        database_client.path = new_localized_path
        self.assertEqual(database_client.path, expected_path)

    def test_write_meta(self):
        """Test the write_meta function for the FileDatabase."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_write_meta')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'DatabaseKey1': 'Value1', 'DatabaseKey2': 2.3},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_file = os.path.join(database_client.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        database_client.write_meta()
        self.assertTrue(os.path.exists(meta_file))

    def test_read_meta(self):
        """Test the read_meta function for the FileDatabase."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_file = os.path.join(database_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_client.read_meta()
        self.assertDictEqual(database_instance.meta,
                             {"DatabaseKey1": "Value1", "DatabaseKey2": 2.3})

    def test_read_meta_overwrite(self):
        """Test the read_meta function for the FileDatabase overwriting data."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_overwrite')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'ShouldNotSeeKey': 'ShouldNotSeeValue'},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_file = os.path.join(database_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_client.read_meta()
        self.assertDictEqual(database_client.instance.meta,
                             {"DatabaseKey1": "Value1", "DatabaseKey2": 2.3})

    def test_read_meta_empty(self):
        """Test the read_meta function for the FileDatabase with empty file."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_empty')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'ShouldNotSeeKey': 'ShouldNotSeeValue'},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_file = os.path.join(database_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_client.read_meta()
        self.assertDictEqual(database_client.instance.meta, {})

    def test_read_meta_no_file(self):
        """Test the read_meta function for the FileDatabase with no file."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_no_file')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'ShouldNotSeeKey': 'ShouldNotSeeValue'},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_file = os.path.join(database_client.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        database_client.read_meta()
        self.assertTrue(os.path.exists(meta_file))
        self.assertDictEqual(database_client.instance.meta, {})

    def test_read_meta_bad_file(self):
        """Test the read_meta function for the FileDatabase."""
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_bad_file')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'KeyYouWillNotSee': 'ValueYouWillNotSee'},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_file = os.path.join(database_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_client.read_meta()
        self.assertDictEqual(database_client.instance.meta, {})

    def test_get_meta(self):
        """Test get_meta function"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_write_meta')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        meta_value = database_client.get_meta('Key2')
        self.assertEqual(meta_value, 1234)

    def test_get_meta_bad_key(self):
        """Test get_meta function with a bad key"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_write_meta')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(KeyError) as exc:
            _ = database_client.get_meta('Key2345')
        self.assertTrue('Key2345' in str(exc.exception))

    def test_set_meta(self):
        """Test set_meta function"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_write_meta')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        database_client.set_meta('Key3', 'NewValue')

        altered_collection = self.session.query(FileDatabase).get(database_id)
        self.assertEqual(altered_collection.meta.get('Key3', None), 'NewValue')

    def test_set_meta_new_value(self):
        """Test get_meta function with a new key"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_write_meta_new_value')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        database_client.set_meta('NewKey', 'AddedValue')

        altered_collection = self.session.query(FileDatabase).get(database_id)
        self.assertEqual(altered_collection.meta.get('NewKey', None), 'AddedValue')

    def test_new_collection(self):
        """Test the new_collection function."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        base_files_root_dir = os.path.join(self.test_files_base, 'test_new_collection')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_collection')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        collection_client = database_client.new_collection()
        new_file_collection = self.session.query(FileCollection).get(collection_client.instance.id)
        self.assertTrue(new_file_collection is not None)
        self.assertTrue(os.path.exists(os.path.join(database_client.path, str(collection_client.instance.id))))

    def test_new_collection_with_files(self):
        """Test the new_collection function with a list of files to copy."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        base_files_root_dir = os.path.join(self.test_files_base, 'test_new_collection_with_files')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_collection_with_files')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        collection_files = [
            os.path.join(root_dir, 'files', 'file1.txt'),
            os.path.join(root_dir, 'files', 'dir1'),
        ]
        database_client = FileDatabaseClient(self.session, database_id)
        collection_client = database_client.new_collection(items=collection_files)
        new_file_collection = self.session.query(FileCollection).get(collection_client.instance.id)
        self.assertTrue(new_file_collection is not None)
        self.assertTrue(os.path.exists(os.path.join(database_client.path, str(collection_client.instance.id))))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'dir1')))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'dir1', 'file2.txt')))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'dir1', 'dir2')))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'dir1', 'dir2', 'file3.txt')))

    def test_new_collection_with_meta(self):
        """Test the new_collection function with meta."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        base_files_root_dir = os.path.join(self.test_files_base, 'test_new_collection_with_meta')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_collection_with_meta')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        collection_client = database_client.new_collection(meta={'Key1': 'Val1', 'Key2': 'Val2'})
        new_file_collection = self.session.query(FileCollection).get(collection_client.instance.id)
        self.assertTrue(new_file_collection is not None)
        self.assertDictEqual(collection_client.instance.meta, {'Key1': 'Val1', 'Key2': 'Val2'})

    @mock.patch('tethysext.atcore.models.file_database.file_collection_client.FileCollectionClient.add_item')
    def test_new_collection_fail_no_commit(self, mock_new_collection):
        """Test the new_collection function when something fails."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        base_files_root_dir = os.path.join(self.test_files_base, 'test_new_collection_fail_no_commit')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_collection_fail_no_commit')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        pre_count = self.session.query(FileCollection).count()
        collection_files = [
            os.path.join(root_dir, 'files', 'file1.txt'),
            os.path.join(root_dir, 'files', 'dir1'),
        ]
        mock_new_collection.side_effect = FileNotFoundError('Mock Exception')
        with self.assertRaises(FileNotFoundError):
            _ = database_client.new_collection(items=collection_files)
        post_count = self.session.query(FileCollection).count()
        self.assertEqual(pre_count, post_count)

    def test_get_collection(self):
        """Test getting a collection."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'test_get_collection')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        collection_client = database_client.get_collection(collection_id)
        self.assertEqual(collection_client.instance.meta, {'TestKey1': 'TestVal1'})

    def test_get_collection_does_not_exist(self):
        """Test getting a collection that doesn't exist."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_collection')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            _ = database_client.get_collection(collection_id)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_get_collection_not_owned_by_this_db(self):
        """Test getting a collection not owned by this database."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        second_database_id = uuid.UUID('{03e7a676-db7c-4cd9-95f0-97e7b97072a4}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_collection')
        second_root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_collection2')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_database_instance(
            database_id=second_database_id, root_directory=second_root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=second_database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            _ = database_client.get_collection(collection_id)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_export_collection(self):
        """Test exporting a collection."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        base_files_root_dir = os.path.join(self.test_files_base,  'test_export_collection')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_export_collection')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        export_directory = os.path.join(self.test_files_base, 'temp', 'exported_files', 'test_export_collection')
        database_client.export_collection(collection_id, export_directory)
        self.assertTrue(os.path.exists(export_directory))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'file5.txt')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir1')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir1', 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir1', 'file2.txt')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir1', 'dir2')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir1', 'dir2', 'file3.txt')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir3')))
        self.assertTrue(os.path.exists(os.path.join(export_directory, 'dir3', 'file4.txt')))

    def test_get_export_does_not_exist(self):
        """Test exporting a collection that does not exist."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'test_get_export_does_not_exist')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        export_directory = os.path.join(self.test_files_base, 'temp', 'exported_files',
                                        'test_get_export_does_not_exist')
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            database_client.export_collection(collection_id, export_directory)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_get_export_not_owned_by_this_db(self):
        """Test exporting a collection not owned by this database."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        second_database_id = uuid.UUID('{03e7a676-db7c-4cd9-95f0-97e7b97072a4}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_export_not_owned_by_this_db')
        second_root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_export_not_owned_by_this_db2')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_database_instance(
            database_id=second_database_id, root_directory=second_root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=second_database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        export_directory = os.path.join(self.test_files_base, 'temp', 'exported_files',
                                        'test_get_export_not_owned_by_this_db')
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            database_client.export_collection(collection_id, export_directory)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_duplicate_collection(self):
        """Test duplicating a collection"""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        base_files_root_dir = os.path.join(self.test_files_base,  'test_duplicate_collection')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_duplicate_collection')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        collection_client = FileCollectionClient(self.session, collection_id)
        new_file_collection = database_client.duplicate_collection(collection_id)
        self.assertDictEqual(new_file_collection.instance.meta, collection_client.instance.meta)
        self.assertEqual(new_file_collection.instance.file_database_id, collection_client.instance.file_database_id)
        self.assertTrue(new_file_collection.path.startswith(database_client.path))

    def test_duplicate_collection_bad_id(self):
        """Test duplicating a collection with a bad id."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        second_database_id = uuid.UUID('{03e7a676-db7c-4cd9-95f0-97e7b97072a4}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_duplicate_collection_bad_id')
        second_root_dir = os.path.join(self.test_files_base, 'temp', 'test_duplicate_collection_bad_id')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_database_instance(
            database_id=second_database_id, root_directory=second_root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=second_database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            database_client.duplicate_collection(collection_id)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_delete_collection(self):
        """Test deleting a file collection"""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        base_files_root_dir = os.path.join(self.test_files_base,  'test_delete_collection')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_delete_collection')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        shutil.copytree(base_files_root_dir, root_dir)
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        collection_client = FileCollectionClient(self.session, collection_id)
        collection_path = collection_client.path
        database_client.delete_collection(collection_id)
        self.assertTrue(
            self.session.query(FileCollection).filter_by(id=collection_id, file_database_id=database_id).count() == 0
        )
        self.assertFalse(os.path.exists(collection_path))

    def test_get_delete_does_not_exist(self):
        """Test deleting a file collection that doesn't exist."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        second_database_id = uuid.UUID('{03e7a676-db7c-4cd9-95f0-97e7b97072a4}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_delete_does_not_exist')
        second_root_dir = os.path.join(self.test_files_base, 'temp', 'test_get_delete_does_not_exist')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_database_instance(
            database_id=second_database_id, root_directory=second_root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        _ = self.get_collection_instance(
            collection_id=collection_id, database_id=second_database_id,
            collection_meta={'TestKey1': 'TestVal1'}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            database_client.delete_collection(collection_id)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_get_delete_not_owned_by_this_db(self):
        """Test deleting a FileCollection that doesn't belong to the database"""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'test_get_delete_not_owned_by_this_db')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(FileCollectionNotFoundError) as exc:
            database_client.delete_collection(collection_id)
        self.assertTrue(f'Collection with id "{str(collection_id)}" could not be found with '
                        f'this database.' in str(exc.exception))

    def test_deleted_database_client(self):
        """Test Generating a FileDatabaseClient from and existing FileDatabase."""
        database_id = uuid.UUID('{4b62335d-5b43-4e3b-bba7-07cd88cc2205}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_deleted_database_client')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir, database_meta={},
        )
        database_client = FileDatabaseClient(self.session, database_id)
        database_client._FileDatabaseClient__deleted = True
        with self.assertRaises(UnboundFileDatabaseError) as exc:
            _ = database_client.instance
        self.assertTrue('The file database has been deleted.' in str(exc.exception))

    def test_bad_database_client(self):
        """Test Generating a FileDatabaseClient from and existing FileDatabase."""
        database_id = uuid.UUID('{4b62335d-5b43-4e3b-bba7-07cd88cc2205}')
        database_client = FileDatabaseClient(self.session, database_id)
        with self.assertRaises(FileDatabaseNotFoundError) as exc:
            _ = database_client.instance
        self.assertTrue(f'FileDatabase with id "{str(database_id)}" not found.' in str(exc.exception))
