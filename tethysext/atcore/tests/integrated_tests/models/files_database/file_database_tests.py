from tethysext.atcore.models.file_database import FileDatabase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FileDatabaseTests(SqlAlchemyTestCase):

    def test_database_round_trip(self):
        """Test a round trip through the database for the FileDatabase model"""
        new_instance = FileDatabase(meta={"TestKey": "TestValue"})
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileDatabase).get(new_instance.id)
        self.assertDictEqual(new_instance.meta, instance_from_db.meta)
