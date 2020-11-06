import os
from unittest import mock
import uuid

from tethysext.atcore.models.file_database import FileCollection, FileDatabase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FileCollectionTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         'files', 'file_collection_tests')
        )

    def get_database_and_collection(self, database_id, root_directory, collection_id,
                                    database_meta=None, collection_meta=None):
        if database_meta is None:
            database_meta = {}
        if collection_meta is None:
            collection_meta = {}

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

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_path_property(self, mock_db_insert, mock_insert):
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        collection_id = uuid.UUID('{a5a99e1c-3d17-4fbb-88b7-d3d264e825ff}')
        root_dir = os.path.join(self.test_files_base, 'test_path_property')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={}, collection_meta={}
        )
        expected_path = os.path.abspath(os.path.join(root_dir, str(database_id), str(collection_id)))
        self.assertEqual(collection_instance.path, expected_path)

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_files_generator(self, mock_db_insert, mock_insert):
        """Test the file generator works as expected."""
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')
        collection_id = uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        root_dir = os.path.join(self.test_files_base, 'test_files_generator')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={}, collection_meta={}
        )

        files = [x for x in collection_instance.files]
        expected_files = [
            os.path.join('file5.txt'),
            os.path.join('dir3', 'file4.txt'),
            os.path.join('dir1', 'file2.txt'),
            os.path.join('dir1', 'file1.txt'),
            os.path.join('dir1', 'dir2', 'file3.txt')
        ]
        self.assertListEqual(files, expected_files)

    def test_database_round_trip(self):
        """Test the FileCollection in a round trip through the database"""
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_database_round_trip')
        database_instance = FileDatabase(root_directory=root_dir, meta={"TestKey": "TestValue"})
        self.session.add(database_instance)
        self.session.commit()
        new_instance = FileCollection(file_database_id=database_instance.id,
                                      meta={"TestKey": "TestValue"})
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileCollection).get(new_instance.id)
        self.assertEqual(new_instance.file_database_id, instance_from_db.file_database_id)
        self.assertEqual(new_instance.path, instance_from_db.path)
        self.assertEqual(new_instance.meta, instance_from_db.meta)

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_write_meta(self, mock_db_insert, mock_insert):
        """Test the the write_meta functionality"""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_write_meta')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23}
        )
        meta_file = os.path.join(collection_instance.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        collection_instance.write_meta()
        self.assertTrue(os.path.exists(meta_file))

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_read_meta(self, mock_db_insert, mock_insert):
        """Test the the read_meta functionality."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={}
        )
        meta_file = os.path.join(collection_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_instance.read_meta()
        self.assertDictEqual(collection_instance.meta,
                             {'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_read_meta_overwrite(self, mock_db_insert, mock_insert):
        """Test the the read_meta functionality."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_overwrite')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'ThisKey': 'ShouldNotExist'}
        )
        meta_file = os.path.join(collection_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_instance.read_meta()
        self.assertDictEqual(collection_instance.meta,
                             {'Key1': 'StringValue', 'Key2': 1234, 'Key3': 1.23})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_read_meta_empty(self, mock_db_insert, mock_insert):
        """Test the the read_meta functionality with an empty file."""
        database_id = uuid.UUID('{12856d36-cb6d-4a5e-84a6-6ee3696a67f1}')
        collection_id = uuid.UUID('{eab613c8-da79-48e0-9db0-1ac854efd966}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_empty')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={"DatabaseKey1": "Value1", "DatabaseKey2": 2.3}
        )
        meta_file = os.path.join(collection_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_instance.read_meta()
        self.assertDictEqual(collection_instance.meta, {})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_read_meta_no_file(self, mock_db_insert, mock_insert):
        """Test the the read_meta functionality with no meta file."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_no_file')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={}
        )
        meta_file = os.path.join(collection_instance.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        collection_instance.read_meta()
        self.assertTrue(os.path.exists(meta_file))
        self.assertDictEqual(collection_instance.meta, {})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    @mock.patch('tethysext.atcore.models.file_database.file_collection._file_collection_after_insert')
    def test_read_meta_bad_file(self, mock_db_insert, mock_insert):
        """Test the the read_meta functionality when the JSON is invalid."""
        database_id = uuid.UUID('{0aeeacc5-9a36-4006-b786-8b5089826bbc}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_bad_file')
        _, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'KeyYouWillNotSee': 'ValueYouWillNotSee'}
        )
        meta_file = os.path.join(collection_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        collection_instance.read_meta()
        self.assertDictEqual(collection_instance.meta, {})

    def test_file_collection_after_insert(self):
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_file_database_after_insert')
        _, _ = self.get_database_and_collection(
            database_id=database_id,  collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'Value1', 'Key2': 2.7}
        )
        meta_file = os.path.join(root_dir, str(database_id), str(collection_id), '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        with open(meta_file, 'r') as f:
            file_text = f.read()
            expected_text = '{"Key1": "Value1", "Key2": 2.7}'
            self.assertEqual(file_text, expected_text)

    def test_file_collection_after_update(self):
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_file_database_after_update')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id,  collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'Value1', 'Key2': 2.7}
        )
        meta_file = os.path.join(root_dir, str(database_id), str(collection_id), '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        with open(meta_file, 'r') as f:
            file_text = f.read()
            expected_text = '{"Key1": "Value1", "Key2": 2.7}'
            self.assertEqual(file_text, expected_text)
        collection_instance.meta["Key1"] = 1.73
        collection_instance.meta["Key2"] = "Value4"
        self.session.commit()
        with open(meta_file, 'r') as f:
            file_text = f.read()
            expected_text = '{"Key1": 1.73, "Key2": "Value4"}'
            self.assertEqual(file_text, expected_text)

    def test_file_collection_after_delete(self):
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        collection_id = uuid.UUID('{120e22d4-32f2-4dac-832c-6995746f0fe7}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_file_database_after_delete')
        _, collection_instance = self.get_database_and_collection(
            database_id=database_id,  collection_id=collection_id,
            root_directory=root_dir, database_meta={},
            collection_meta={'Key1': 'Value1', 'Key2': 2.7}
        )
        meta_file = os.path.join(root_dir, str(database_id), str(collection_id), '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))

        self.session.delete(collection_instance)
        self.session.commit()
        self.assertFalse(os.path.exists(meta_file))
        self.assertFalse(os.path.exists(os.path.join(root_dir, str(database_id), str(collection_id))))
