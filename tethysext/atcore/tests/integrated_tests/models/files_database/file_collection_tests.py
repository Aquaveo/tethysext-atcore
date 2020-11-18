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

    def test_database_round_trip(self):
        """Test the FileCollection in a round trip through the database"""
        database_id = uuid.UUID('{bb7c67a9-9d51-4baa-96a9-d38d56b8c79c}')

        database_instance = FileDatabase(
            id=database_id,  # We need to set the id here for the test path.
            root_directory='.',
        )

        self.session.add(database_instance)
        self.session.commit()

        new_instance = FileCollection(file_database_id=database_id,
                                      meta={"TestKey": "TestValue"})
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileCollection).get(new_instance.id)
        self.assertEqual(new_instance.file_database_id, instance_from_db.file_database_id)
        self.assertEqual(new_instance.meta, instance_from_db.meta)
