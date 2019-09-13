from unittest import mock

from django.test import RequestFactory

from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep, ResourceWorkflowResult


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        # Custom setup here
        self.workflow = ResourceWorkflow(name='bar')

        # Build the steps and save in the workflow
        # Status will be set dynamically to allow for easy testing.
        self.step_1 = ResourceWorkflowStep(name='foo', help='step_1', order=1)
        self.step_2 = ResourceWorkflowStep(name='bar', help='step_2', order=2)
        self.step_3 = ResourceWorkflowStep(name='baz', help='step_3', order=3)
        self.step_4 = ResourceWorkflowStep(name='invalid_step', help='invalid step 4', order=4)
        self.workflow.steps = [self.step_1, self.step_2, self.step_3]

        # Build the results and save in the workflow
        self.result_1 = ResourceWorkflowResult(name='foo', description='lorem_1', _data={'baz': 1})
        self.result_2 = ResourceWorkflowResult(name='bar', description='lorem_2', _data={'baz': 2})
        self.result_3 = ResourceWorkflowResult(name='baz', description='lorem_3', _data={'baz': 3})
        self.result_4 = ResourceWorkflowResult(name='invalid_step', description='invalid step 4', _data={'baz': 4})
        self.workflow.results = [self.result_1, self.result_2, self.result_3]

        self.session.add(self.workflow)

        self.session.commit()

    def test___str__(self):
        ret = str(self.workflow)
        self.assertEqual(f'<ResourceWorkflow name="bar" id="{self.workflow.id}">', ret)

    def test_get_next_step_no_steps(self):
        self.workflow.steps = []
        idx, ret = self.workflow.get_next_step()
        self.assertIsNone(ret)
        self.assertEqual(0, idx)

    def test_get_next_step_no_root_status(self):
        self.step_1.set_status(ResourceWorkflowStep.ROOT_STATUS_KEY, None)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(0, idx)
        self.assertEqual(self.step_1, ret)

    def test_get_next_step_multiple_first_complete(self):
        self.workflow.steps[0].set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.workflow.steps[1].set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_COMPLETE)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(2, idx)
        self.assertEqual(self.step_3, ret)

    def test_get_next_step_multiple_step_all_complete(self):
        self.workflow.steps[0].set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.workflow.steps[1].set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_COMPLETE)
        self.workflow.steps[2].set_status(self.step_3.ROOT_STATUS_KEY, self.step_3.STATUS_COMPLETE)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(2, idx)
        self.assertEqual(self.step_3, ret)

    def test_get_next_step_one_step_complete(self):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.workflow.steps = [self.step_1]
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(0, idx)
        self.assertEqual(self.step_1, ret)

    def test_get_next_step_one_step_not_complete(self):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_PENDING)
        self.workflow.steps = [self.step_1]
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(0, idx)
        self.assertEqual(self.step_1, ret)

    def test_get_next_step_multiple_steps_non_COMPLETE_complete_statuses(self):
        self.workflow.steps[0].set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_SUBMITTED)
        self.workflow.steps[1].set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_APPROVED)
        self.workflow.steps[2].set_status(self.step_3.ROOT_STATUS_KEY, self.step_3.STATUS_PENDING)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(2, idx)
        self.assertEqual(self.step_3, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_status_first_step_pending(self, mock_next_step):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_PENDING)
        mock_next_step.return_value = (0, self.step_1)
        ret = self.workflow.get_status()
        self.assertEqual(self.workflow.STATUS_PENDING, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_status_first_step_not_pending(self, mock_next_step):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_ERROR)
        self.step_2.set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_PENDING)
        mock_next_step.return_value = (0, self.step_1)
        ret = self.workflow.get_status()
        self.assertEqual(self.workflow.STATUS_ERROR, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_status_not_first_step(self, mock_next_step):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.step_2.set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_PENDING)
        mock_next_step.return_value = (1, self.step_2)
        ret = self.workflow.get_status()
        self.assertEqual(self.workflow.STATUS_CONTINUE, ret)

    def test_get_adjacent_steps_first_step(self):
        prev_step, next_step = self.workflow.get_adjacent_steps(self.step_1)
        self.assertIsNone(prev_step)
        self.assertEqual(next_step, self.step_2)

    def test_get_adjacent_steps_middle_step(self):
        prev_step, next_step = self.workflow.get_adjacent_steps(self.step_2)
        self.assertEqual(prev_step, self.step_1)
        self.assertEqual(next_step, self.step_3)

    def test_get_adjacent_steps_last_step(self):
        prev_step, next_step = self.workflow.get_adjacent_steps(self.step_3)
        self.assertEqual(prev_step, self.step_2)
        self.assertIsNone(next_step)

    def test_get_adjacent_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.get_adjacent_steps, self.step_4)

    def test_get_previous_steps_first_step(self):
        ret = self.workflow.get_previous_steps(self.step_1)
        self.assertListEqual([], ret)

    def test_get_previous_steps_middle_step(self):
        ret = self.workflow.get_previous_steps(self.step_2)
        self.assertListEqual([self.step_1], ret)

    def test_get_previous_steps_last_step(self):
        ret = self.workflow.get_previous_steps(self.step_3)
        self.assertListEqual([self.step_1, self.step_2], ret)

    def test_get_previous_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.get_previous_steps, self.step_4)

    def test_get_next_steps(self):
        ret = self.workflow.get_next_steps(self.step_1)
        self.assertListEqual([self.step_2, self.step_3], ret)

    def test_get_next_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.get_next_steps, self.step_4)

    def test_reset_next_steps(self):
        self.step_2.set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_COMPLETE)
        self.step_3.set_status(self.step_3.ROOT_STATUS_KEY, self.step_3.STATUS_ERROR)

        self.workflow.reset_next_steps(self.step_1)

        self.assertEqual(self.step_2.STATUS_PENDING, self.step_2.get_status(self.step_2.ROOT_STATUS_KEY))
        self.assertEqual(self.step_3.STATUS_PENDING, self.step_3.get_status(self.step_3.ROOT_STATUS_KEY))

    def test_reset_next_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.reset_next_steps, self.step_4)


class ResourceWorkflowLockTests(SqlAlchemyTestCase):

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
    def test_release_user_lock_locked_not_given_request_user_permissed_user(self, mock_hp):
        request = self.rf.get('/foo/bar')
        request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ret = self.workflow.release_user_lock(request)

        self.assertFalse(ret)
        self.assertEqual('otheruser', self.workflow._user_lock)
        mock_hp.assert_called_with(request, 'can_override_user_locks')

    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)
    def test_release_user_lock_locked_for_all_users_permissed_user(self, mock_hp):
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
