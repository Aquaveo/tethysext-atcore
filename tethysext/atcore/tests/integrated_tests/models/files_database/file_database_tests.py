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
        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         'files', 'file_database_tests')
        )

    def get_database_and_collection(self, database_id, root_directory, database_meta=None):
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

    def test_database_round_trip(self):
        new_instance = FileDatabase(root_directory='.', meta={"TestKey": "TestValue"})
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileDatabase).get(new_instance.id)
        self.assertEqual(new_instance.root_directory, instance_from_db.root_directory)
        self.assertEqual(new_instance.meta, instance_from_db.meta)
