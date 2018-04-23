"""
********************************************************************************
* Name: app_users.py
* Author: nswain
* Created On: April 23, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.permissions.app_users import PermissionsGenerator
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


class PermissionsGeneratorTests(TethysTestCase):

    def setUp(self):
        self.apm = AppPermissionsManager('foo')
        self.pg = PermissionsGenerator(self.apm)

    def tearDown(self):
        pass

    def test_add_permissions_for(self):
        self.pg.add_permissions_for(self.apm._APP_A_PERMS, ['fake-permission', 'another-fake-permission'])
        self.assertIn(self.apm._APP_A_PERMS, self.pg.custom_permissions)
        self.assertIn('fake-permission', self.pg.custom_permissions[self.apm._APP_A_PERMS])
        self.assertIn('another-fake-permission', self.pg.custom_permissions[self.apm._APP_A_PERMS])

    def test_add_permissions_for_invalid_permission_group(self):
        self.assertRaises(ValueError, self.pg.add_permissions_for, 'not-a-valid-perm-group', [])

    def test_add_permissions_for_invalid_permissions(self):
        self.assertRaises(ValueError, self.pg.add_permissions_for, self.apm._APP_A_PERMS, 'not-a-list')

    def test_generate(self):
        perms = self.pg.generate()
        self.assertEqual(9, len(perms))
