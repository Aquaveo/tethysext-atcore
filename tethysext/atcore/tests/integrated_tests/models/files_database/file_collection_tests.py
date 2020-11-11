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
        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         'files', 'file_collection_tests')
        )

    def get_database_and_collection(self, database_id, root_directory, collection_id,
                                    database_meta=None, collection_meta=None):
        database_meta = database_meta or {}
        collection_meta = collection_meta or {}
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

    def test_database_round_trip(self):
        """Test the FileCollection in a round trip through the database"""
        database_id = uuid.UUID('{bb7c67a9-9d51-4baa-96a9-d38d56b8c79c}')
        collection_id = uuid.UUID('{c675abc8-59b6-4ecd-a568-c01c9c1ec49f}')
        root_dir = os.path.join(self.test_files_base, 'test_database_round_trip')
        database_instance, collection_instance = self.get_database_and_collection(
            database_id=database_id, collection_id=collection_id,
            root_directory=root_dir
        )
        new_instance = FileCollection(file_database_id=database_id,
                                      meta={"TestKey": "TestValue"})
        self.session.add(new_instance)
        self.session.commit()
        instance_from_db = self.session.query(FileCollection).get(new_instance.id)
        self.assertEqual(new_instance.file_database_id, instance_from_db.file_database_id)
        self.assertEqual(new_instance.meta, instance_from_db.meta)
