import unittest
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users import AppUsersBase, Resource, Organization

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


class OrganizationResourceTests(unittest.TestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        # Test users
        self.resource1 = Resource(
            name="resource1",
            description="a resource",
            status="available",
        )

        self.resource2 = Resource(
            name="resource2",
            description="a resource",
            status="available",
        )

        self.resource3 = Resource(
            name="resource3",
            description="a resource",
            status="available",
        )

        # Test Organizations
        self.organization1 = Organization(
            name="organization1",
            license=Organization.LICENSES.STANDARD
        )

        self.organization2 = Organization(
            name="organization2",
            license=Organization.LICENSES.STANDARD
        )

        # Add users to organizations
        self.organization1.resources.extend([self.resource1, self.resource2])
        self.organization2.resources.extend([self.resource2, self.resource3])

        # Commit to db
        self.session.add(self.resource1)
        self.session.add(self.resource2)
        self.session.add(self.resource3)
        self.session.add(self.organization1)
        self.session.add(self.organization2)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_resource_organizations(self):
        resource1_organizations = self.resource1.organizations
        resource2_organizations = self.resource2.organizations
        resource3_organizations = self.resource3.organizations

        self.assertEqual(1, len(resource1_organizations))
        self.assertIn(self.organization1, resource1_organizations)
        self.assertNotIn(self.organization2, resource1_organizations)

        self.assertEqual(2, len(resource2_organizations))
        self.assertIn(self.organization1, resource2_organizations)
        self.assertIn(self.organization2, resource2_organizations)

        self.assertEqual(1, len(resource3_organizations))
        self.assertNotIn(self.organization1, resource3_organizations)
        self.assertIn(self.organization2, resource3_organizations)

    def test_organization_resources(self):
        organization1_resources = self.organization1.resources
        organization2_resources = self.organization2.resources

        self.assertEqual(2, len(organization1_resources))
        self.assertIn(self.resource1, organization1_resources)
        self.assertIn(self.resource2, organization1_resources)
        self.assertNotIn(self.resource3, organization1_resources)

        self.assertEqual(2, len(organization2_resources))
        self.assertIn(self.resource2, organization2_resources)
        self.assertIn(self.resource3, organization2_resources)
        self.assertNotIn(self.resource1, organization2_resources)
