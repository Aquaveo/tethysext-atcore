import os
import uuid

from tethysext.atcore.models.file_database import FileCollection, FileCollectionClient, FileDatabase
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
        pass

    def test_path_property(self):
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        collection_id = uuid.UUID('{a5a99e1c-3d17-4fbb-88b7-d3d264e825ff}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_path_property')
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
        self.assertDictEqual(collection_client.meta,
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
        self.assertDictEqual(collection_client.meta,
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
        self.assertDictEqual(collection_client.meta, {})

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
        self.assertDictEqual(collection_client.meta, {})

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
        self.assertDictEqual(collection_client.meta, {})
