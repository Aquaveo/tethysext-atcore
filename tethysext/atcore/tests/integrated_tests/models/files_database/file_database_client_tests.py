import os
import uuid

from tethysext.atcore.models.file_database import FileDatabase, FileDatabaseClient
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
        self.assertDictEqual(database_client.meta,
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
        self.assertDictEqual(database_client.meta, {})

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
        self.assertDictEqual(database_client.meta, {})

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
        self.assertDictEqual(database_client.meta, {})
