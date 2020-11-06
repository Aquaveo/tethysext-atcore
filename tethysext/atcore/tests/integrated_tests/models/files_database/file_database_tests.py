import os
from unittest import mock
import uuid

from tethysext.atcore.models.file_database import FileDatabase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FileDatabaseTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         'files', 'file_database_tests')
        )

    def get_database_instance(self, database_id, root_directory, database_meta=None):
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

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_path_property(self, mock_insert):
        """Test the path property of the file collection works correctly."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_path_property')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir, database_meta={},
        )
        expected_path = os.path.abspath(os.path.join(root_dir, str(database_id)))
        self.assertEqual(database_instance.path, expected_path)

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_setting_localized_path(self, mock_insert):
        """Test the setting a localized root directory."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_path_property')
        database_instance = self.get_database_instance(
            database_id=database_id,  root_directory=root_dir, database_meta={}
        )
        new_localized_path = os.path.abspath(os.path.join(root_dir, 'new_localized_directory'))
        expected_path = os.path.abspath(os.path.join(new_localized_path, str(database_instance.id)))

        database_instance.path = new_localized_path
        self.assertEqual(database_instance.path, expected_path)

    def test_database_round_trip(self):
        new_instance = FileDatabase(root_directory='.', meta={"TestKey": "TestValue"})
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileDatabase).get(new_instance.id)
        self.assertEqual(new_instance.root_directory, instance_from_db.root_directory)
        self.assertEqual(new_instance.meta, instance_from_db.meta)

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_write_meta(self, mock_insert):
        """Test the write_meta function for the FileDatabase."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_write_meta')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'DatabaseKey1': 'Value1', 'DatabaseKey2': 2.3},
        )
        meta_file = os.path.join(database_instance.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        database_instance.write_meta()
        self.assertTrue(os.path.exists(meta_file))

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_read_meta(self, mock_insert):
        """Test the read_meta function for the FileDatabase."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={},
        )
        meta_file = os.path.join(database_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_instance.read_meta()
        self.assertDictEqual(database_instance.meta,
                             {"DatabaseKey1": "Value1", "DatabaseKey2": 2.3})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_read_meta_overwrite(self, mock_insert):
        """Test the read_meta function for the FileDatabase overwriting data."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_overwrite')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'ShouldNotSeeKey': 'ShouldNotSeeValue'},
        )
        meta_file = os.path.join(database_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_instance.read_meta()
        self.assertDictEqual(database_instance.meta,
                             {"DatabaseKey1": "Value1", "DatabaseKey2": 2.3})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_read_meta_empty(self, mock_insert):
        """Test the read_meta function for the FileDatabase with empty file."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_empty')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'ShouldNotSeeKey': 'ShouldNotSeeValue'},
        )
        meta_file = os.path.join(database_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_instance.read_meta()
        self.assertDictEqual(database_instance.meta, {})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_read_meta_no_file(self, mock_insert):
        """Test the read_meta function for the FileDatabase with no file."""
        database_id = uuid.UUID('{f0699b82-8ff4-4646-ab2b-cb43f137c3ac}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_no_file')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'ShouldNotSeeKey': 'ShouldNotSeeValue'},
        )
        meta_file = os.path.join(database_instance.path, '__meta__.json')
        if os.path.exists(meta_file):
            os.remove(meta_file)
        self.assertFalse(os.path.exists(meta_file))
        database_instance.read_meta()
        self.assertTrue(os.path.exists(meta_file))
        self.assertDictEqual(database_instance.meta, {})

    @mock.patch('tethysext.atcore.models.file_database.file_database._file_database_after_insert')
    def test_read_meta_bad_file(self, mock_insert):
        """Test the read_meta function for the FileDatabase."""
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        root_dir = os.path.join(self.test_files_base, 'test_read_meta_bad_file')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'KeyYouWillNotSee': 'ValueYouWillNotSee'},
        )
        meta_file = os.path.join(database_instance.path, '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        database_instance.read_meta()
        self.assertDictEqual(database_instance.meta, {})

    def test_file_database_after_insert(self):
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_file_database_after_insert')
        _ = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'Value1', 'Key2': 2.7},
        )
        meta_file = os.path.join(root_dir, str(database_id), '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        with open(meta_file, 'r') as f:
            file_text = f.read()
            expected_text = '{"Key1": "Value1", "Key2": 2.7}'
            self.assertEqual(file_text, expected_text)

    def test_file_database_after_update(self):
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_file_database_after_update')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'Value1', 'Key2': 2.7},
        )
        meta_file = os.path.join(root_dir, str(database_id), '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))
        with open(meta_file, 'r') as f:
            file_text = f.read()
            expected_text = '{"Key1": "Value1", "Key2": 2.7}'
            self.assertEqual(file_text, expected_text)
        database_instance.meta["Key1"] = 1.73
        database_instance.meta["Key2"] = "Value4"
        self.session.commit()
        with open(meta_file, 'r') as f:
            file_text = f.read()
            expected_text = '{"Key1": 1.73, "Key2": "Value4"}'
            self.assertEqual(file_text, expected_text)

    def test_file_database_after_delete(self):
        database_id = uuid.UUID('{e5bc841e-eeb7-4211-951f-d7e5a4ad08f2}')
        root_dir = os.path.join(self.test_files_base, 'temp', 'test_file_database_after_delete')
        database_instance = self.get_database_instance(
            database_id=database_id, root_directory=root_dir,
            database_meta={'Key1': 'Value1', 'Key2': 2.7},
        )
        meta_file = os.path.join(root_dir, str(database_id), '__meta__.json')
        self.assertTrue(os.path.exists(meta_file))

        self.session.delete(database_instance)
        self.session.commit()
        self.assertFalse(os.path.exists(meta_file))
        self.assertFalse(os.path.exists(os.path.join(root_dir, str(database_id))))
