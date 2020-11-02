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
            root_directory=os.path.join('..', '..', '..', 'files', 'file_database_tests', 'file_generator_test')
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
        expected_path = os.path.join('..', '..', '..', 'files', 'file_database_tests',
                                     'file_generator_test', str(self.file_database_instance.id))
        self.assertEqual(self.instance.path, expected_path)

    def test_files_generator(self):
        files = [x for x in self.instance.files]
        self.assertListEqual(files, [])
