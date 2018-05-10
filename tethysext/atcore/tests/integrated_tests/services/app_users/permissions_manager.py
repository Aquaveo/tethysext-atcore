"""
********************************************************************************
* Name: permissions_manager.py
* Author: nswain
* Created On: May 10, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.contrib.auth.models import User, Group
from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.models.app_users import AppUser, initialize_app_users_db
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.services.app_users.licenses import Licenses
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.tests import TEST_DB_URL


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    # Initialize db with staff user
    initialize_app_users_db(connection)


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class AppPermissionsManagerTests(TethysTestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)
        self.roles = Roles()
        self.licenses = Licenses()

        # Normal user
        self.username = "user"
        self.user = AppUser(
            username=self.username,
            role=self.roles.ORG_USER
        )
        self.session.add(self.user)
        self.session.commit()

        self.django_user = User.objects.create_user(
            username=self.username,
            password="pass"
        )

        # Staff User
        self.staff_username = "staff"
        self.staff_django_user = User.objects.create_superuser(
            username=self.staff_username,
            email="teva@aquaveo.com",
            password="pass"
        )
        self.staff_app_user = self.session.query(AppUser).filter(AppUser.username == AppUser.STAFF_USERNAME).one()

        # Permissions manager setup
        self.namespace = 'foo'
        self.apm = AppPermissionsManager(self.namespace)
        self.num_permissions_groups = 9

        # Create one of the groups for testing
        self.group = Group.objects.get_or_create(name=self.apm.STANDARD_USER_PERMS)

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_list(self):
        permissions_groups = self.apm.list()
        self.assertEqual(self.num_permissions_groups, len(permissions_groups))
        for pg in permissions_groups:
            self.assertNotIn(self.namespace, pg)

    def test_list_with_namespace(self):
        permissions_groups = self.apm.list(with_namespace=True)
        self.assertEqual(self.num_permissions_groups, len(permissions_groups))
        for pg in permissions_groups:
            self.assertIn(self.namespace, pg)

    def test_get_permission_group_for(self):
        for role in self.roles.list():
            for license in self.licenses.list():
                val = self.apm.get_permissions_group_for(role, license)

                if role != self.roles.DEVELOPER:
                    self.assertIsNotNone(val)
                else:
                    self.assertIsNone(val)

    def test_display_name_for(self):
        for role in self.roles.list():
            for license in self.licenses.list():
                permission_group = self.apm.get_permissions_group_for(role, license)
                display_name = self.apm.get_display_name_for(permission_group)
                self.assertIsNotNone(display_name)

    def test_get_rank_for(self):
        for role in self.roles.list():
            for license in self.licenses.list():
                permission_group = self.apm.get_permissions_group_for(role, license)
                rank = self.apm.get_rank_for(permission_group)
                self.assertIsNotNone(rank)

    def test_add_permissions_group(self):
        self.apm.add_permissions_group(self.user, self.apm.STANDARD_USER_PERMS)
        django_user = User.objects.get(username=self.username)
        groups = django_user.groups.values_list('name', flat=True)
        self.assertIn(self.apm.STANDARD_USER_PERMS, groups)

    def test_add_permissions_group_is_staff(self):
        self.apm.add_permissions_group(self.staff_app_user, self.apm.STANDARD_USER_PERMS)

    def test_remove_permissions_group(self):
        django_user = User.objects.get(username=self.username)
        my_group = Group.objects.get(name=self.apm.STANDARD_USER_PERMS)
        my_group.user_set.add(django_user)

        self.apm.remove_permissions_group(self.user, self.apm.STANDARD_USER_PERMS)
        d_user = User.objects.get(username=self.username)
        groups = d_user.groups.values_list('name', flat=True)
        self.assertNotIn(self.apm.STANDARD_USER_PERMS, groups)

    def test_remove_permissions_group_is_staff(self):
        self.apm.remove_permissions_group(self.staff_app_user, self.apm.STANDARD_USER_PERMS)

    def test_remove_all_permissions_groups(self):
        django_user = User.objects.get(username=self.username)

        my_group = Group.objects.get(name=self.apm.STANDARD_USER_PERMS)
        my_group.user_set.add(django_user)

        my_other_group, _ = Group.objects.get_or_create(name=self.apm.STANDARD_ADMIN_PERMS)
        my_other_group.user_set.add(django_user)

        my_another_group, _ = Group.objects.get_or_create(name="boo")
        my_another_group.user_set.add(django_user)

        self.apm.remove_all_permissions_groups(self.user)
        d_user = User.objects.get(username=self.username)
        groups = d_user.groups.values_list('name', flat=True)
        self.assertNotIn(self.apm.STANDARD_USER_PERMS, groups)
        self.assertNotIn(self.apm.STANDARD_ADMIN_PERMS, groups)
        self.assertIn("boo", groups)

    def test_remove_all_permissions_groups_is_staff(self):
        self.apm.remove_all_permissions_groups(self.staff_app_user)

    def test_get_all_permissions_groups_for(self):
        django_user = User.objects.get(username=self.username)

        my_group = Group.objects.get(name=self.apm.STANDARD_USER_PERMS)
        my_group.user_set.add(django_user)

        my_other_group, _ = Group.objects.get_or_create(name=self.apm.STANDARD_ADMIN_PERMS)

        my_another_group, _ = Group.objects.get_or_create(name="boo")
        my_another_group.user_set.add(django_user)

        permission_groups = self.apm.get_all_permissions_groups_for(self.user)
        self.assertIn(self.apm.STANDARD_USER_PERMS, permission_groups)
        self.assertNotIn(self.apm.STANDARD_ADMIN_PERMS, permission_groups)
        self.assertNotIn("boo", permission_groups)

    def test_get_all_permissions_groups_for_is_staff(self):
        Group.objects.get_or_create(name=self.apm.STANDARD_ADMIN_PERMS)
        Group.objects.get_or_create(name="boo")
        permission_groups = self.apm.get_all_permissions_groups_for(self.staff_app_user)
        self.assertIn(self.apm.STANDARD_USER_PERMS, permission_groups)
        self.assertIn(self.apm.STANDARD_ADMIN_PERMS, permission_groups)
        self.assertNotIn("boo", permission_groups)

    def test_get_all_permissions_groups_for_as_display_name(self):
        django_user = User.objects.get(username=self.username)

        my_group = Group.objects.get(name=self.apm.STANDARD_USER_PERMS)
        my_group.user_set.add(django_user)

        my_other_group, _ = Group.objects.get_or_create(name=self.apm.STANDARD_ADMIN_PERMS)

        my_another_group, _ = Group.objects.get_or_create(name="boo")
        my_another_group.user_set.add(django_user)

        permission_groups = self.apm.get_all_permissions_groups_for(self.user, as_display_name=True)
        self.assertIn(self.apm.get_display_name_for(self.apm.STANDARD_USER_PERMS), permission_groups)
        self.assertNotIn(self.apm.get_display_name_for(self.apm.STANDARD_ADMIN_PERMS), permission_groups)
        self.assertNotIn("boo", permission_groups)

    def test_assign_user_permission(self):
        self.apm.assign_user_permission(self.user, self.roles.ORG_USER, self.licenses.STANDARD)
        django_user = User.objects.get(username=self.username)
        groups = django_user.groups.values_list('name', flat=True)
        self.assertIn(self.apm.STANDARD_USER_PERMS, groups)

    def test_assign_user_permission_is_staff(self):
        self.apm.assign_user_permission(self.staff_app_user, self.roles.ORG_USER, self.licenses.STANDARD)

    def test_remove_user_permission(self):
        django_user = User.objects.get(username=self.username)

        my_group = Group.objects.get(name=self.apm.STANDARD_USER_PERMS)
        my_group.user_set.add(django_user)
        self.apm.remove_user_permission(self.user, self.roles.ORG_USER, self.licenses.STANDARD)

        d_user = User.objects.get(username=self.username)
        groups = d_user.groups.values_list('name', flat=True)
        self.assertNotIn(self.apm.STANDARD_USER_PERMS, groups)

    def test_remove_user_permission_is_staff(self):
        self.apm.remove_user_permission(self.staff_app_user, self.roles.ORG_USER, self.licenses.STANDARD)
