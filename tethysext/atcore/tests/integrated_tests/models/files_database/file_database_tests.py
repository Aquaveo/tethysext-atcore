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
