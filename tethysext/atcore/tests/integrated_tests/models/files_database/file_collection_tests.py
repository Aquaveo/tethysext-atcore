import os
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
        self.file_database_instance = FileDatabase(
            id=uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}'),  # We need to set the id here for the test path.
            root_directory=os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                        '..', '..', '..',
                                                        'files', 'file_database_tests', 'file_generator_test'))
        )
        self.session.add(self.file_database_instance)
        self.session.commit()
        self.instance = FileCollection(
            file_database_id=self.file_database_instance.id,
            meta='{"JsonKey": "JsonValue"}',
        )
        self.session.add(self.instance)
        self.session.commit()

    def test_path_property(self):
        """Test the path property of the file collection works correctly."""
        expected_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                     '..', '..', '..', 'files', 'file_database_tests',
                                                     'file_generator_test', str(self.file_database_instance.id)))
        self.assertEqual(self.instance.path, expected_path)

    def test_files_generator(self):
        """Test the file generator works as expected."""
        files = [x for x in self.instance.files]
        expected_files = [
            os.path.join(self.instance.path, 'file5.txt'),
            os.path.join(self.instance.path, 'dir3', 'file4.txt'),
            os.path.join(self.instance.path, 'dir1', 'file2.txt'),
            os.path.join(self.instance.path, 'dir1', 'file1.txt'),
            os.path.join(self.instance.path, 'dir1', 'dir2', 'file3.txt')
        ]
        self.assertListEqual(files, expected_files)

    def test_database_round_trip(self):
        new_instance = FileCollection(file_database_id=self.file_database_instance.id,
                                      meta='{"TestKey": "TestValue"}')
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileCollection).get(new_instance.id)
        self.assertEqual(new_instance.file_database_id, instance_from_db.file_database_id)
        self.assertEqual(new_instance.path, instance_from_db.path)
        self.assertEqual(new_instance.meta, instance_from_db.meta)
