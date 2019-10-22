from unittest import mock
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.mixins import UserLockMixin


class LockedThing(UserLockMixin):
    pass


class UserLockMixinTests(TethysTestCase):

    def setUp(self):
        # Custom setup here
        self.instance = LockedThing()

        self.django_user = UserFactory()
        self.django_user.save()

        self.rf = RequestFactory()

    def test_acquire_user_lock_django_user(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user

        ret = self.instance.acquire_user_lock(request)

        self.assertTrue(ret)
        self.assertEqual(self.django_user.username, self.instance._user_lock)

    def test_acquire_user_lock_django_user_already_locked_for_given_user(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.django_user.username

        ret = self.instance.acquire_user_lock(request)

        self.assertTrue(ret)
        self.assertEqual(self.django_user.username, self.instance._user_lock)

    def test_acquire_user_lock_django_user_already_locked_not_given_user(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = 'otheruser'

        ret = self.instance.acquire_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual('otheruser', self.instance._user_lock)

    def test_acquire_user_lock_django_user_already_locked_for_all_users(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.acquire_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual(self.instance.LOCKED_FOR_ALL_USERS, self.instance._user_lock)

    def test_acquire_user_lock_for_all_users(self):
        ret = self.instance.acquire_user_lock()

        self.assertTrue(ret)
        self.assertEqual(self.instance.LOCKED_FOR_ALL_USERS, self.instance._user_lock)

    def test_acquire_user_lock_for_all_users_already_locked_for_all_users(self):
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.acquire_user_lock()

        self.assertTrue(ret)
        self.assertEqual(self.instance.LOCKED_FOR_ALL_USERS, self.instance._user_lock)

    def test_acquire_user_lock_for_all_users_already_locked_for_specific_user(self):
        self.instance._user_lock = self.django_user.username

        ret = self.instance.acquire_user_lock()

        self.assertFalse(ret)
        self.assertEqual(self.django_user.username, self.instance._user_lock)

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_not_locked(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user

        ret = self.instance.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.instance._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_locked_with_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.django_user.username

        ret = self.instance.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.instance._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_locked_not_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = 'otheruser'

        ret = self.instance.release_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual('otheruser', self.instance._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_release_user_lock_locked_not_given_request_user_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = 'otheruser'

        ret = self.instance.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.instance._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_release_user_lock_locked_for_all_users_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.instance._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_locked_for_all_users_not_admin_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.release_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual(self.instance.LOCKED_FOR_ALL_USERS, self.instance._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    def test_user_lock_initial(self):
        ret = self.instance.user_lock

        self.assertIsNone(ret)

    def test_user_lock_set(self):
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.user_lock

        self.assertEqual(self.instance.LOCKED_FOR_ALL_USERS, ret)

    def test_is_user_locked_initial(self):
        ret = self.instance.is_user_locked

        self.assertFalse(ret)

    def test_is_user_locked_empty_string(self):
        self.instance._user_lock = ''

        ret = self.instance.is_user_locked

        self.assertFalse(ret)

    def test_is_user_locked_user(self):
        self.instance._user_lock = self.django_user.username

        ret = self.instance.is_user_locked

        self.assertTrue(ret)

    def test_is_user_locked_for_all_users(self):
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.is_user_locked

        self.assertTrue(ret)

    def test_is_locked_for_all_users_initial(self):
        ret = self.instance.is_locked_for_all_users

        self.assertFalse(ret)

    def test_is_locked_for_all_users_locked(self):
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.is_locked_for_all_users

        self.assertTrue(ret)

    def test_is_locked_for_all_users_username(self):
        self.instance._user_lock = self.django_user.username

        ret = self.instance.is_locked_for_all_users

        self.assertFalse(ret)

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_is_locked_for_request_user_locked_with_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.django_user.username

        ret = self.instance.is_locked_for_request_user(request)

        self.assertFalse(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_is_locked_for_request_user_locked_not_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = 'otheruser'

        ret = self.instance.is_locked_for_request_user(request)

        self.assertTrue(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_is_locked_for_request_user_locked_not_given_request_user_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = 'otheruser'

        ret = self.instance.is_locked_for_request_user(request)

        self.assertFalse(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_is_locked_for_request_user_locked_for_all_users_not_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.is_locked_for_request_user(request)

        self.assertTrue(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_is_locked_for_request_user_locked_for_all_users_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.instance._user_lock = self.instance.LOCKED_FOR_ALL_USERS

        ret = self.instance.is_locked_for_request_user(request)

        self.assertFalse(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')
