from unittest import mock
from django.test import RequestFactory
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflow


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowLockMethodsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        # Custom setup here
        self.workflow = ResourceWorkflow(name='bar')
        self.session.add(self.workflow)
        self.session.commit()

        self.django_user = UserFactory()
        self.django_user.save()

        self.rf = RequestFactory()

    def test_acquire_user_lock_django_user(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user

        ret = self.workflow.acquire_user_lock(request)

        self.assertTrue(ret)
        self.assertEqual(self.django_user.username, self.workflow._user_lock)

    def test_acquire_user_lock_django_user_already_locked_for_given_user(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ret = self.workflow.acquire_user_lock(request)

        self.assertTrue(ret)
        self.assertEqual(self.django_user.username, self.workflow._user_lock)

    def test_acquire_user_lock_django_user_already_locked_not_given_user(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ret = self.workflow.acquire_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual('otheruser', self.workflow._user_lock)

    def test_acquire_user_lock_django_user_already_locked_for_all_users(self):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.acquire_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, self.workflow._user_lock)

    def test_acquire_user_lock_for_all_users(self):
        ret = self.workflow.acquire_user_lock()

        self.assertTrue(ret)
        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, self.workflow._user_lock)

    def test_acquire_user_lock_for_all_users_already_locked_for_all_users(self):
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.acquire_user_lock()

        self.assertTrue(ret)
        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, self.workflow._user_lock)

    def test_acquire_user_lock_for_all_users_already_locked_for_specific_user(self):
        self.workflow._user_lock = self.django_user.username

        ret = self.workflow.acquire_user_lock()

        self.assertFalse(ret)
        self.assertEqual(self.django_user.username, self.workflow._user_lock)

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_not_locked(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user

        ret = self.workflow.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_locked_with_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ret = self.workflow.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_locked_not_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ret = self.workflow.release_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual('otheruser', self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_release_user_lock_locked_not_given_request_user_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ret = self.workflow.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_release_user_lock_locked_for_all_users_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.release_user_lock(request)

        self.assertTrue(ret)
        self.assertIsNone(self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_locked_for_all_users_not_admin_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.release_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    def test_user_lock_initial(self):
        ret = self.workflow.user_lock

        self.assertIsNone(ret)

    def test_user_lock_set(self):
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.user_lock

        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, ret)

    def test_is_user_locked_initial(self):
        ret = self.workflow.is_user_locked

        self.assertFalse(ret)

    def test_is_user_locked_empty_string(self):
        self.workflow._user_lock = ''

        ret = self.workflow.is_user_locked

        self.assertFalse(ret)

    def test_is_user_locked_user(self):
        self.workflow._user_lock = self.django_user.username

        ret = self.workflow.is_user_locked

        self.assertTrue(ret)

    def test_is_user_locked_for_all_users(self):
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.is_user_locked

        self.assertTrue(ret)

    def test_is_locked_for_all_users_initial(self):
        ret = self.workflow.is_locked_for_all_users

        self.assertFalse(ret)

    def test_is_locked_for_all_users_locked(self):
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.is_locked_for_all_users

        self.assertTrue(ret)

    def test_is_locked_for_all_users_username(self):
        self.workflow._user_lock = self.django_user.username

        ret = self.workflow.is_locked_for_all_users

        self.assertFalse(ret)

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_is_locked_for_request_user_locked_with_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ret = self.workflow.is_locked_for_request_user(request)

        self.assertFalse(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_is_locked_for_request_user_locked_not_given_request_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ret = self.workflow.is_locked_for_request_user(request)

        self.assertTrue(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_is_locked_for_request_user_locked_not_given_request_user_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ret = self.workflow.is_locked_for_request_user(request)

        self.assertFalse(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_is_locked_for_request_user_locked_for_all_users_not_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.is_locked_for_request_user(request)

        self.assertTrue(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_is_locked_for_request_user_locked_for_all_users_permitted_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ret = self.workflow.is_locked_for_request_user(request)

        self.assertFalse(ret)
        mock_hp.assert_called_with(request, 'can_override_user_locks')
