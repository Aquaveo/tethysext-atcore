import unittest
import uuid
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users import AppUsersBase, Organization

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


class OrganizationTests(unittest.TestCase):
    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.name = "test_organization"
        self.active = True

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_create_organization(self):
        organization = Organization(
            name=self.name,
            active=self.active,
        )

        self.session.add(organization)
        self.session.commit()

        all_organization_count = self.session.query(Organization).count()
        all_organization = self.session.query(Organization).all()

        self.assertEqual(all_organization_count, 1)
        for organization in all_organization:
            self.assertEqual(organization.name, self.name)
            self.assertEqual(organization.active, self.active)
            self.assertEqual(organization.type, Organization.GENERIC_ORG_TYPE)
            self.assertIsInstance(organization.id, uuid.UUID)
