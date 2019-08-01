from unittest import mock
from django.http import HttpResponseRedirect, HttpRequest
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
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


class WorkflowViewTests(SqlAlchemyTestCase):

    def setUp(self):
        self.workflow = mock.MagicMock(spec=ResourceWorkflow)
        self.workflow.steps = [
            ResourceWorkflowStep(
                id=1,
                help='help1',
                name='name1',
                type='type1'),
            ResourceWorkflowStep(
                id=2,
                help='help2',
                name='name2',
                type='type2'
            )]

    def tearDown(self):
        # super().tearDown()
        pass

    # def test_get_context(self):
    #     request = mock.MagicMock(spec=HttpRequest)
    #     session = mock.MagicMock()
    #     resource = mock.MagicMock()
    #     context = mock.MagicMock(spec=ModelDatabase)
    #     model_db = mock.MagicMock(spec=ResourceWorkflowStep)
    #     workflow_id = ''
    #     step_id = ''
    #     # In workflow_step_controller, self.get_sessionmaker method not implemented.
    #     ret = ResourceWorkflowView().get_context(request, session, resource, context, model_db, workflow_id, step_id)

    # def test_get_context_message(self):
    #     # Or without message
    #     # Fail, complete and other
    #     pass

    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_step_url_name(self, mock_app):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        mock_request = mock.MagicMock(path='apps/and/such')
        mock_workflow = mock.MagicMock(type='my_type')

        ret = ResourceWorkflowView().get_step_url_name(mock_request, mock_workflow)

        self.assertEqual('my_workspace:my_type_workflow_step', ret)

    def test_build_step_cards(self):
        self.workflow.steps.append(ResourceWorkflowStep())

        steps = ResourceWorkflowView().build_step_cards(self.workflow)

        self.assertEquals(len(self.workflow.steps), len(steps))
        self.assertEquals(self.workflow.steps[0].id, steps[0]['id'])
        self.assertEquals(self.workflow.steps[0].name, steps[0]['name'])
        self.assertEquals(self.workflow.steps[0].help, steps[0]['help'])
        self.assertEquals(self.workflow.steps[0].type, steps[0]['type'])
        self.assertEquals('pending', steps[0]['status'])
        self.assertEquals(True, steps[0]['link'])

        self.assertEquals(self.workflow.steps[1].id, steps[1]['id'])
        self.assertEquals(self.workflow.steps[1].name, steps[1]['name'])
        self.assertEquals(self.workflow.steps[1].help, steps[1]['help'])
        self.assertEquals(self.workflow.steps[1].type, steps[1]['type'])
        self.assertEquals('pending', steps[1]['status'])
        self.assertEquals(False, steps[1]['link'])

    def test_build_step_cards_no_steps(self):
        workflow = mock.MagicMock(spec=ResourceWorkflow)
        workflow.steps = []

        steps = ResourceWorkflowView().build_step_cards(workflow)

        self.assertEqual(workflow.steps, steps)

    # def test_save_step_data(self):
    #     request = mock.MagicMock(spec=HttpRequest)
    #     session = mock.MagicMock()
    #     resource = mock.MagicMock(spec=Resource)
    #     workflow = mock.MagicMock(spec=ResourceWorkflow)
    #     step = mock.MagicMock(spec=ResourceWorkflowStep)
    #     # In workflow_step_controller, self.get_sessionmaker method not implemented.
    #     ret = ResourceWorkflowView().save_step_data(request, session, resource, workflow, step)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_user_has_active_role_active(self, mock_gpm, mock_permission):
        mock_gpm.return_value = mock.MagicMock(spec=AppPermissionsManager)
        mock_permission.return_value = True
        mock_request = mock.MagicMock()
        self.workflow.steps[0].active_roles = ['has_advanced_user_role']

        ret = ResourceWorkflowView().user_has_active_role(mock_request, self.workflow.steps[0])

        self.assertTrue(ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_user_has_active_role_not_active(self, mock_gpm, mock_permission):
        mock_gpm.return_value = mock.MagicMock(spec=AppPermissionsManager)
        mock_permission.return_value = False
        mock_request = mock.MagicMock()
        self.workflow.steps[0].active_roles = ['has_advanced_user_role']

        ret = ResourceWorkflowView().user_has_active_role(mock_request, self.workflow.steps[0])

        self.assertFalse(ret)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_user_has_active_role_not_defined(self, mock_gpm):
        mock_gpm.return_value = mock.MagicMock(spec=AppPermissionsManager)
        mock_request = mock.MagicMock()
        self.workflow.steps[0].active_roles = []

        ret = ResourceWorkflowView().user_has_active_role(mock_request, self.workflow.steps[0])

        self.assertTrue(ret)

    def test_validate_step_valid(self):
        was_thrown = False

        try:
            ResourceWorkflowView().validate_step(None, None, ResourceWorkflowStep(), None, None)
        except TypeError:
            was_thrown = True

        self.assertFalse(was_thrown)

    def test_validate_step_invalid(self):
        with self.assertRaises(TypeError) as e:
            ResourceWorkflowView().validate_step(None, None, InvalidStep(), None, None)
        self.assertEqual(
            'Invalid step type for view: "InvalidStep". Must be one of "ResourceWorkflowStep".',
            str(e.exception))

    # # mock_get_adj_step returns nothing instead of 2 mocks
    # @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_adjacent_steps')
    # @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.get_step')
    # @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.get_workflow')
    # def test_on_get(self, mock_get_workflow, mock_get_step, mock_get_adj_step):
    #     mock_get_workflow.return_value = mock.MagicMock(spec=ResourceWorkflow)
    #     mock_get_step.return_value = mock.MagicMock(spec=ResourceWorkflow)
    #     mock_get_adj_step.return_value = mock.MagicMock(spec=ResourceWorkflowStep), \
    #                                      mock.MagicMock(spec=ResourceWorkflowStep)
    #     request = mock.MagicMock(spec=HttpRequest)
    #     resource = mock.MagicMock()
    #
    #     ret = ResourceWorkflowView().on_get(request, None, resource, 'workflow_id', 'step_id')

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.reset_next_steps')
    def test_process_step_data_dirty(self, _):
        mock_request = mock.MagicMock()
        mock_request.POST = 'submit'
        step = mock.MagicMock(dirty=True)
        previous_url = './previous'
        next_url = './next'

        ret = ResourceWorkflowView().process_step_data(mock_request, mock.MagicMock(), step, None, None,
                                                       previous_url, next_url)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(previous_url, ret['location'])
        self.assertFalse(step.dirty)

    def test_process_step_data_not_dirty(self):
        mock_request = mock.MagicMock()
        mock_request.POST = 'next-submit'
        step = mock.MagicMock(dirty=False)
        previous_url = './previous'
        next_url = './next'

        ret = ResourceWorkflowView().process_step_data(mock_request, None, step, None, None, previous_url, next_url)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(next_url, ret['location'])
        self.assertFalse(step.dirty)

    def test_navigate_only_complete(self):
        step = mock.MagicMock(spec=ResourceWorkflowStep)
        step.get_status.return_value = step.STATUS_COMPLETE
        request = mock.MagicMock(spec=HttpRequest)
        request.POST = 'next-submit'
        current_url = './current'
        previous_url = './previous'
        next_url = './next'

        response = ResourceWorkflowView().navigate_only(request, step, current_url, next_url, previous_url)

        self.assertEqual(next_url, response['location'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.messages')
    def test_navigate_only_not_complete_with_next_submit(self, mock_messages):
        request = mock.MagicMock(spec=HttpRequest)
        step = mock.MagicMock(spec=ResourceWorkflowStep)
        request.POST = 'next-submit'
        current_url = './current'
        previous_url = './previous'
        next_url = './next'

        response = ResourceWorkflowView().navigate_only(request, step, current_url, next_url, previous_url)

        mock_messages.warning.assert_called_with(request, 'You do not have the permission to complete this step.')
        self.assertEqual(current_url, response['location'])
