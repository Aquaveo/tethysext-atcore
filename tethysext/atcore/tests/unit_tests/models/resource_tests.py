import datetime
import unittest
import uuid
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users import AppUsersBase, Resource

from tethysext.atcore.tests import APP_USER_TEST_DB


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(APP_USER_TEST_DB)
    connection = engine.connect()
    transaction = connection.begin()
    AppUsersBase.metadata.create_all(connection)

    # If you want to insert fixtures to the DB, do it here


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.name = "test_organization"
        self.description = "Bad Description"
        self.status = "PROCESSING"
        self.creation_date = datetime.datetime.utcnow()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_create_organization(self):
        resource = Resource(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date,
        )

        self.session.add(resource)
        self.session.commit()

        all_resources_count = self.session.query(Resource).count()
        all_resources = self.session.query(Resource).all()

        self.assertEqual(all_resources_count, 1)
        for resource in all_resources:
            self.assertEqual(resource.name, self.name)
            self.assertEqual(resource.description, self.description)
            self.assertEqual(resource.date_created, self.creation_date)
            self.assertEqual(resource.status, self.status)
            self.assertFalse(resource.public)
            self.assertEqual(resource.type, Resource.TYPE)
            self.assertIsInstance(resource.id, uuid.UUID)
