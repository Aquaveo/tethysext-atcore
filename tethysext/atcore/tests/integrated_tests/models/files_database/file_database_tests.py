import os

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
        self.instance = FileDatabase(
            root_directory=os.path.join('..', '..', '..', 'files', 'file_database_tests', 'file_generator_test')
        )
        self.session.add(self.instance)
        self.session.commit()

    def test_path_property(self):
        expected_path = os.path.join('..', '..', '..', 'files', 'file_database_tests',
                                     'file_generator_test', str(self.instance.id))
        self.assertEqual(self.instance.path, expected_path)

    def test_setting_localized_path(self):
        new_localized_path = os.path.join('..', '..', '..', 'files', 'file_database_tests_local',
                                          'file_generator_test')
        self.instance.path = new_localized_path
        self.assertEqual(self.instance.path, os.path.join(new_localized_path, str(self.instance.id)))

    def test_database_round_trip(self):
        new_instance = FileDatabase(root_directory='.', meta='{"TestKey": "TestValue"}')
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileDatabase).get(new_instance.id)
        self.assertEqual(new_instance.root_directory, instance_from_db.root_directory)
        self.assertEqual(new_instance.meta, instance_from_db.meta)
