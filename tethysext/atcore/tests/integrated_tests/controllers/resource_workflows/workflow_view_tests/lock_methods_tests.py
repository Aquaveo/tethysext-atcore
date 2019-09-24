"""
********************************************************************************
* Name: lock_methods_tests.py
* Author: nswain
* Created On: September 23, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock

from django.http import HttpRequest
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class InvalidStep(ResourceWorkflowView):
    pass


class WorkflowViewLockMethodsTests(SqlAlchemyTestCase):
    current_url = './current'
    previous_url = './previous'
    next_url = './next'

    def setUp(self):
        super().setUp()
        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        self.django_user = UserFactory()
        self.django_user.save()

        self.workflow = ResourceWorkflow(name='foo')

        # Step 1
        self.step1 = ResourceWorkflowStep(
            name='name1',
            help='help1',
            order=1,
        )
        self.workflow.steps.append(self.step1)

        # Step 2
        self.step2 = ResourceWorkflowStep(
            name='name2',
            help='help2',
            order=2
        )
        self.workflow.steps.append(self.step2)

        # Step 3
        self.step3 = ResourceWorkflowStep(
            name='name3',
            help='help3',
            order=3
        )
        self.workflow.steps.append(self.step3)

        self.session.add(self.workflow)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def assert_log_failed_to_acquire(self, mock_log):
        """
        Verify that a message was logged indicating a lock was not acquired.
        """
        mock_log.warning.assert_called()
        call_args = mock_log.warning.call_args_list
        self.assertIn('attempted to acquire', call_args[0][0][0])
        self.assertIn('unsuccessful', call_args[0][0][0])

    def assert_log_successfully_acquired(self, mock_log):
        """
        Verify that a message was logged indicating a lock was acquired successfully.
        """
        mock_log.debug.assert_called()
        call_args = mock_log.debug.call_args_list
        self.assertIn('successfully acquired a user lock', call_args[0][0][0])

    def assert_log_failed_to_release(self, mock_log):
        """
        Verify that a message was logged indicating a lock was not released.
        """
        mock_log.warning.assert_called()
        call_args = mock_log.warning.call_args_list
        self.assertIn('attempted to release', call_args[0][0][0])
        self.assertIn('unsuccessful', call_args[0][0][0])

    def assert_log_successfully_released(self, mock_log):
        """
        Verify that a message was logged indicating a lock was released successfully.
        """
        mock_log.debug.assert_called()
        call_args = mock_log.debug.call_args_list
        self.assertIn('successfully released a user lock', call_args[0][0][0])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=False)
    def test_build_workflow_lock_display_options_not_locked(self, _):
        self.request.user = self.django_user
        self.workflow._user_lock = None  # Not locked

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'warning',
            'message': 'The workflow is not locked.',
            'show': False
        }

        self.assertDictEqual(expected, ret)

    # to mock import in ResourceWofkflow.is_locked_for_request_user method
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)  # to mock import in model methods
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=False)
    def test_build_workflow_lock_display_options_locked_for_request_user(self, _, __):
        self.request.user = self.django_user
        self.workflow._user_lock = self.django_user.username  # Locked for request user

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'warning',
            'message': 'The workflow is locked for editing for all other users.',
            'show': True
        }

        self.assertDictEqual(expected, ret)

    # to mock import in ResourceWofkflow.is_locked_for_request_user method
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=False)
    def test_build_workflow_lock_display_options_locked_for_other_user(self, _, __):
        self.request.user = self.django_user
        self.workflow._user_lock = 'some-other-username'  # Locked for a different user

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'warning',
            'message': 'The workflow is locked for editing by another user.',
            'show': True
        }

        self.assertDictEqual(expected, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=False)
    def test_build_workflow_lock_display_options_locked_for_all_users(self, _):
        self.request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS  # Locked for all users

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'info',
            'message': 'The workflow is locked for editing for all users.',
            'show': True
        }

        self.assertDictEqual(expected, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=True)
    def test_build_workflow_lock_display_options_locked_for_request_user_permitted_user(self, _):
        self.request.user = self.django_user
        self.workflow._user_lock = self.django_user.username  # Locked for request user

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'warning',
            'message': f'The workflow is locked for editing for user: {self.django_user.username}',
            'show': True
        }

        self.assertDictEqual(expected, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=True)
    def test_build_workflow_lock_display_options_locked_for_other_user_permitted_user(self, _):
        self.request.user = self.django_user
        self.workflow._user_lock = 'some-other-username'  # Locked for a different user

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'warning',
            'message': 'The workflow is locked for editing for user: some-other-username',
            'show': True
        }

        self.assertDictEqual(expected, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission', return_value=True)
    def test_build_workflow_lock_display_options_locked_for_all_users_permitted_user(self, _):
        self.request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS  # Locked for all users

        ret = ResourceWorkflowView().build_workflow_lock_display_options(self.request, self.workflow)

        expected = {
            'style': 'info',
            'message': 'The workflow is locked for editing for all users.',
            'show': True
        }

        self.assertDictEqual(expected, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=False)  # not active user
    def test_process_lock_options_on_init_not_active_user(self, _, mock_rulal, mock_aulal):
        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step1)

        mock_rulal.assert_not_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)  # active user
    def test_process_lock_options_on_init_release_lock(self, _, mock_rulal, mock_aulal):
        self.step1.options['release_workflow_lock_on_init'] = True

        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step1)

        mock_rulal.assert_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)  # active user
    def test_process_lock_options_on_init_lock_required_step_not_complete(self, _, mock_rulal, mock_aulal):
        self.step1.options['workflow_lock_required'] = True
        self.step1.set_status(status=self.step1.STATUS_PENDING)

        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step1)

        mock_rulal.assert_not_called()
        mock_aulal.assert_called_with(self.request, self.session, self.workflow)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)  # active user
    def test_process_lock_options_on_init_lock_required_step_complete(self, _, mock_rulal, mock_aulal):
        self.step1.options['workflow_lock_required'] = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)

        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step1)

        mock_rulal.assert_not_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)  # active user
    def test_process_lock_options_on_init_lock_when_finished_workflow_complete(self, _, mock_rulal, mock_aulal):
        self.workflow.lock_when_finished = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)
        self.step2.set_status(status=self.step2.STATUS_COMPLETE)
        self.step3.set_status(status=self.step3.STATUS_COMPLETE)

        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step3)

        mock_rulal.assert_not_called()
        mock_aulal.assert_called_with(self.request, self.session, self.workflow, for_all_users=True)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)  # active user
    def test_process_lock_options_on_init_lock_when_finished_workflow_not_complete(self, _, mock_rulal, mock_aulal):
        self.workflow.lock_when_finished = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)
        self.step2.set_status(status=self.step2.STATUS_COMPLETE)
        self.step3.set_status(status=self.step3.STATUS_PENDING)

        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step3)

        mock_rulal.assert_not_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)  # active user
    def test_process_lock_options_on_init_all_enabled(self, _, mock_rulal, mock_aulal):
        self.step3.options['workflow_lock_required'] = True
        self.step3.options['release_workflow_lock_on_init'] = True
        self.workflow.lock_when_finished = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)
        self.step2.set_status(status=self.step2.STATUS_COMPLETE)
        self.step3.set_status(status=self.step3.STATUS_COMPLETE)

        ResourceWorkflowView().process_lock_options_on_init(self.request, self.session, self.step3)

        mock_rulal.assert_called()
        mock_aulal.assert_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    def test_lock_options_after_submission_release_lock_step_complete(self, mock_rulal, mock_aulal):
        self.step1.options['release_workflow_lock_on_init'] = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)

        ResourceWorkflowView().process_lock_options_after_submission(self.request, self.session, self.step1)

        mock_rulal.assert_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    def test_lock_options_after_submission_release_lock_step_not_complete(self, mock_rulal, mock_aulal):
        self.step1.options['release_workflow_lock_on_init'] = True
        self.step1.set_status(status=self.step1.STATUS_PENDING)

        ResourceWorkflowView().process_lock_options_after_submission(self.request, self.session, self.step1)

        mock_rulal.assert_not_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    def test_lock_options_after_submission_lock_when_finished_workflow_complete(self, mock_rulal, mock_aulal):
        self.workflow.lock_when_finished = True
        self.step3.options['release_workflow_lock_on_completion'] = False
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)
        self.step2.set_status(status=self.step2.STATUS_COMPLETE)
        self.step3.set_status(status=self.step3.STATUS_COMPLETE)

        ResourceWorkflowView().process_lock_options_after_submission(self.request, self.session, self.step3)

        mock_rulal.assert_not_called()
        mock_aulal.assert_called_with(self.request, self.session, self.workflow, for_all_users=True)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    def test_lock_options_after_submission_lock_when_finished_workflow_not_complete(self, mock_rulal, mock_aulal):
        self.workflow.lock_when_finished = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)
        self.step2.set_status(status=self.step2.STATUS_COMPLETE)
        self.step3.set_status(status=self.step3.STATUS_PENDING)

        ResourceWorkflowView().process_lock_options_after_submission(self.request, self.session, self.step3)

        mock_rulal.assert_not_called()
        mock_aulal.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'acquire_user_lock_and_log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'release_user_lock_and_log')
    def test_lock_options_after_submission_all_enabled(self, mock_rulal, mock_aulal):
        self.workflow.lock_when_finished = True
        self.step3.options['release_workflow_lock_on_init'] = True
        self.step1.set_status(status=self.step1.STATUS_COMPLETE)
        self.step2.set_status(status=self.step2.STATUS_COMPLETE)
        self.step3.set_status(status=self.step3.STATUS_COMPLETE)

        ResourceWorkflowView().process_lock_options_after_submission(self.request, self.session, self.step3)

        mock_rulal.assert_called()
        mock_aulal.assert_called_with(self.request, self.session, self.workflow, for_all_users=True)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    def test_acquire_user_lock_and_log_not_locked(self, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = None  # not locked

        ResourceWorkflowView().acquire_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertEqual(self.django_user.username, self.workflow.user_lock)
        self.assert_log_successfully_acquired(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    def test_acquire_user_lock_and_log_locked_for_request_user(self, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ResourceWorkflowView().acquire_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertEqual(self.django_user.username, self.workflow.user_lock)
        self.assert_log_successfully_acquired(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    def test_acquire_user_lock_and_log_locked_for_other_user(self, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ResourceWorkflowView().acquire_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertEqual('otheruser', self.workflow.user_lock)
        self.assert_log_failed_to_acquire(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    def test_acquire_user_lock_and_log_all_users_not_locked(self, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = None  # not locked

        ResourceWorkflowView().acquire_user_lock_and_log(self.request, self.session, self.workflow, for_all_users=True)

        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, self.workflow.user_lock)
        self.assert_log_successfully_acquired(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    def test_acquire_user_lock_and_log_all_users_locked_for_request_user(self, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ResourceWorkflowView().acquire_user_lock_and_log(self.request, self.session, self.workflow, for_all_users=True)

        self.assertEqual(self.django_user.username, self.workflow.user_lock)
        self.assert_log_failed_to_acquire(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    def test_acquire_user_lock_and_log_all_users_locked_for_other_user(self, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ResourceWorkflowView().acquire_user_lock_and_log(self.request, self.session, self.workflow, for_all_users=True)

        self.assertEqual('otheruser', self.workflow.user_lock)
        self.assert_log_failed_to_acquire(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_and_log_not_locked(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = None  # not locked

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertIsNone(self.workflow.user_lock)
        self.assert_log_successfully_released(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_and_log_locked_for_request_user(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertIsNone(self.workflow.user_lock)
        self.assert_log_successfully_released(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_and_log_locked_for_other_user(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertEqual('otheruser', self.workflow.user_lock)
        self.assert_log_failed_to_release(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=False)
    def test_release_user_lock_and_log_locked_for_all_users(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertEqual(self.workflow.LOCKED_FOR_ALL_USERS, self.workflow.user_lock)
        self.assert_log_failed_to_release(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)  # permitted user
    def test_release_user_lock_and_log_not_locked_permitted(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = None  # not locked

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertIsNone(self.workflow.user_lock)
        self.assert_log_successfully_released(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)  # permitted user
    def test_release_user_lock_and_log_locked_for_request_user_permitted(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = self.django_user.username

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertIsNone(self.workflow.user_lock)
        self.assert_log_successfully_released(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)  # permitted user
    def test_release_user_lock_and_log_locked_for_other_user_permitted(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = 'otheruser'

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertIsNone(self.workflow.user_lock)
        self.assert_log_successfully_released(mock_log)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.log')
    @mock.patch('tethys_sdk.permissions.has_permission', return_value=True)  # permitted user
    def test_release_user_lock_and_log_locked_for_all_users_permitted(self, _, mock_log):
        self.request.user = self.django_user
        self.workflow._user_lock = self.workflow.LOCKED_FOR_ALL_USERS

        ResourceWorkflowView().release_user_lock_and_log(self.request, self.session, self.workflow)

        self.assertIsNone(self.workflow.user_lock)
        self.assert_log_successfully_released(mock_log)
