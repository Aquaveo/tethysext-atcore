from tethysext.atcore.models.app_users import AppUser, Organization
from tethysext.atcore.services.app_users.roles import Roles

from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class AppUserOrganizationTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        # Test users
        self.user1 = AppUser(
            username="user1",
            role=Roles.ORG_USER,
        )

        self.user2 = AppUser(
            username="user2",
            role=Roles.ORG_USER,
        )

        self.user3 = AppUser(
            username="user3",
            role=Roles.ORG_USER,
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
