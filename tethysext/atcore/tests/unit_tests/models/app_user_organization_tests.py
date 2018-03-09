import unittest
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users import AppUsersBase, AppUser, Organization

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


class AppUserOrganizationTests(unittest.TestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        # Test users
        self.user1 = AppUser(
            username="user1",
            role="viewer",
        )

        self.user2 = AppUser(
            username="user2",
            role="viewer",
        )

        self.user3 = AppUser(
            username="user3",
            role="viewer",
        )

        # Test Organizations
        self.organization1 = Organization(
            name="organization1",
        )

        self.organization2 = Organization(
            name="organization2",
        )

        # Add users to organizations
        self.organization1.members.extend([self.user1, self.user2])
        self.organization2.members.extend([self.user2, self.user3])

        # Commit to db
        self.session.add(self.user1)
        self.session.add(self.user2)
        self.session.add(self.user3)
        self.session.add(self.organization1)
        self.session.add(self.organization2)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_app_user_organizations(self):
        user1_organizations = self.user1.organizations
        user2_organizations = self.user2.organizations
        user3_organizations = self.user3.organizations

        self.assertEqual(1, len(user1_organizations))
        self.assertIn(self.organization1, user1_organizations)
        self.assertNotIn(self.organization2, user1_organizations)

        self.assertEqual(2, len(user2_organizations))
        self.assertIn(self.organization1, user2_organizations)
        self.assertIn(self.organization2, user2_organizations)

        self.assertEqual(1, len(user3_organizations))
        self.assertNotIn(self.organization1, user3_organizations)
        self.assertIn(self.organization2, user3_organizations)

    def test_organization_members(self):
        organization1_members = self.organization1.members
        organization2_members = self.organization2.members

        self.assertEqual(2, len(organization1_members))
        self.assertIn(self.user1, organization1_members)
        self.assertIn(self.user2, organization1_members)
        self.assertNotIn(self.user3, organization1_members)

        self.assertEqual(2, len(organization2_members))
        self.assertIn(self.user2, organization2_members)
        self.assertIn(self.user3, organization2_members)
        self.assertNotIn(self.user1, organization2_members)
