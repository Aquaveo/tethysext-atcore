import os
import shutil
import uuid

from tethysext.atcore.exceptions import UnboundFileCollectionError
from tethysext.atcore.models.file_database import FileCollection, FileCollectionClient, FileDatabase, FileDatabaseClient
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FileCollectionClientTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         'files', 'file_collection_client_tests')
        )

    def get_database_and_collection(self, database_id, root_directory, collection_id,
                                    database_meta=None, collection_meta=None):
        """
        A helper function to generate a FileDatabase and a FileCollection in the database.

        Args:
            database_id (uuid.UUID): a UUID to assign the id for the FileDatabase object
            root_directory (str): root directory for a FileDatabase
            collection_id (uuid.UUID): a UUID to assign the id for the FileCollection object
            database_meta (dict): A dictionary of meta for the FileDatabase object
            collection_meta (dict): A dictionary of meta for the FileCollection object
        """
        database_meta = database_meta or {}
        collection_meta = collection_meta or {}
        database_instance = FileDatabase(
            id=database_id,  # We need to set the id here for the test path.
            root_directory=root_directory,
            meta=database_meta,
        )

        self.session.add(database_instance)
        self.session.commit()

        collection_instance = FileCollection(
            id=collection_id,
            file_database_id=database_id,
            meta=collection_meta,
        )

        self.session.add(collection_instance)
        self.session.commit()

        return database_instance, collection_instance

    def test_new_file_collection_client(self):
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_new_file_collection_client')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        database_client = FileDatabaseClient.new(self.session, root_dir)
        self.assertTrue(self.session.query(FileCollection).count() == 0)
        collection_client = FileCollectionClient.new(self.session, database_client.instance.id)
        self.assertTrue(self.session.query(FileCollection).count() == 1)
        self.assertTrue(os.path.exists(collection_client.path))

    def test_path_property(self):
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        collection_id = uuid.UUID('{a5a99e1c-3d17-4fbb-88b7-d3d264e825ff}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_path_property')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={}, collection_meta={}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        expected_path = os.path.abspath(os.path.join(root_dir, str(database_id), str(collection_id)))
        self.assertEqual(collection_client.path, expected_path)

    def test_files_generator(self):
        """Test the file generator works as expected."""
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'test_files_generator')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={}, collection_meta={}
        )
        collection_client = FileCollectionClient(self.session, collection_id)

        files = [x for x in collection_client.files]
        expected_files = [
            os.path.join('file5.txt'),
            os.path.join('dir3', 'file4.txt'),
            os.path.join('dir1', 'file2.txt'),
            os.path.join('dir1', 'file1.txt'),
            os.path.join('dir1', 'dir2', 'file3.txt')
        ]
        self.assertListEqual(files, expected_files)

    def test_write_meta(self):
        """Test the the write_meta functionality"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_write_meta')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_file = os.path.join(collection_client.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        collection_client.write_meta()
        self.assertTrue(os.path.exists(meta_file))

    def test_read_meta(self):
        """Test the the read_meta functionality."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_file = os.path.join(collection_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_client.read_meta()
        self.assertDictEqual(collection_client.instance.meta,
                             {'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23})

    def test_read_meta_overwrite(self):
        """Test the the read_meta functionality."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_overwrite')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'ThisKey': 'ShouldNotExist'}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_file = os.path.join(collection_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_client.read_meta()
        self.assertDictEqual(collection_client.instance.meta,
                             {'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23})

    def test_read_meta_empty(self):
        """Test the the read_meta functionality with an empty file."""
        database_id = uuid.UUID('{12856d36-cb6d-4a5e-84a6-6ee3696a67f1}')
        collection_id = uuid.UUID('{eab613c8-da79-48e0-9db0-1ac854efd966}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_empty')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={"DatabaseKey1": "Value1", "DatabaseKey2": 2.3}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_file = os.path.join(collection_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_client.read_meta()
        self.assertDictEqual(collection_client.instance.meta, {})

    def test_read_meta_no_file(self):
        """Test the the read_meta functionality with no meta file."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_no_file')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_file = os.path.join(collection_client.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        collection_client.read_meta()
        self.assertTrue(os.path.exists(meta_file))
        self.assertDictEqual(collection_client.instance.meta, {})

    def test_read_meta_bad_file(self):
        """Test the the read_meta functionality when the JSON is invalid."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_bad_file')
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'KeyYouWillNotSee': 'ValueYouWillNotSee'}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_file = os.path.join(collection_client.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_client.read_meta()
        self.assertDictEqual(collection_client.instance.meta, {})

    def test_get_meta(self):
        """Test the the write_meta functionality"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_write_meta')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        meta_value = collection_client.get_meta('Key2')
        self.assertEqual(meta_value, 1234)

    def test_get_meta_bad_key(self):
        """Test the the write_meta functionality"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_write_meta')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        with self.assertRaises(KeyError) as exc:
            _ = collection_client.get_meta('Key2345')
        self.assertTrue('Key2345' in str(exc.exception))

    def test_set_meta(self):
        """Test the the write_meta functionality"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_write_meta')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        collection_client.set_meta('Key3', 'NewValue')

        altered_collection = self.session.query(FileCollection).get(collection_id)
        self.assertEqual(altered_collection.meta.get('Key3', None), 'NewValue')

    def test_set_meta_new_value(self):
        """Test the the write_meta functionality"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_write_meta')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        _ = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        collection_client = FileCollectionClient(self.session, collection_id)
        collection_client.set_meta('NewKey', 'AddedValue')

        altered_collection = self.session.query(FileCollection).get(collection_id)
        self.assertEqual(altered_collection.meta.get('NewKey', None), 'AddedValue')

    def test_collection_delete(self):
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_collection_delete')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        database_client = FileDatabaseClient.new(self.session, root_dir)
        collection_client = FileCollectionClient.new(self.session, database_client.instance.id)
        collection_path = os.path.join(root_dir, str(database_client.instance.id), str(collection_client.instance.id))
        self.assertTrue(os.path.exists(collection_path))
        collection_client.delete()
        self.assertFalse(os.path.exists(collection_path))

        with self.assertRaises(UnboundFileCollectionError) as exc:
            _ = collection_client.path

        self.assertTrue('The collection has been deleted.' in str(exc.exception))

    def test_collection_export(self):
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_collection_export')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        database_client = FileDatabaseClient.new(self.session, root_dir)
        collection_client = FileCollectionClient.new(self.session, database_client.instance.id)
        collection_path = os.path.join(root_dir, str(database_client.instance.id), str(collection_client.instance.id))
        export_path = os.path.join(self.test_files_base, 'temp', 'exported_files', 'test_collection_export')
        if os.path.exists(export_path):
            shutil.rmtree(export_path)
        self.assertTrue(os.path.exists(collection_path))
        collection_client.export(export_path)
        self.assertTrue(os.path.exists(export_path))
        self.assertTrue(os.path.exists(os.path.join(export_path, '__meta__.json')))

    def test_collection_duplicate(self):
        root_dir = os.path.join(self.test_files_base, 'temp',  'test_collection_duplicate')
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir)
        database_client = FileDatabaseClient.new(self.session, root_dir)
        collection_client = FileCollectionClient.new(self.session, database_client.instance.id)
        new_collection_client = collection_client.duplicate()
        new_collection_path = os.path.join(root_dir, database_client.path, str(new_collection_client.instance.id))
        self.assertTrue(new_collection_path == new_collection_client.path)
        self.assertTrue(os.path.exists(new_collection_client.path))

    def test_duplicate_with_files(self):
        pass

    def test_export_with_files(self):
        pass
