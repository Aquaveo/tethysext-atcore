from unittest import mock

from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.mixins import StatusMixin
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.services.app_users.roles import Roles


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class InvalidStep(ResourceWorkflowView):
    pass


class WorkflowViewTests(SqlAlchemyTestCase):
    current_url = './current'
    previous_url = './previous'
    next_url = './next'

    def setUp(self):
        super().setUp()
        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        self.workflow = ResourceWorkflow(name='foo')

        # Step 1
        self.step1 = ResourceWorkflowStep(
            name='name1',
            help='help1',
            order=1
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

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)
    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_context(self, mock_app, mock_uhar):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        resource = mock.MagicMock()
        context = {}
        model_db = mock.MagicMock(spec=ResourceWorkflowStep)
        workflow_id = str(self.workflow.id)
        step_id = str(self.step1.id)

        ret = ResourceWorkflowView().get_context(self.request, self.session, resource, context, model_db,
                                                 workflow_id=workflow_id, step_id=step_id)

        self.assertEqual(self.workflow.id, ret['workflow'].id)
        self.assertEqual(len(self.workflow.steps), len(ret['steps']))
        self.assertEqual(None, ret['previous_step'])
        self.assertEqual(self.step2.id, ret['next_step'].id)
        self.assertEqual('my_workspace:generic_workflow_workflow_step', ret['step_url_name'])
        self.assertIn(self.workflow.name, ret['nav_title'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.messages')
    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_context_error_message(self, mock_app, mock_messages, mock_uhar):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        resource = mock.MagicMock()
        context = {}
        model_db = mock.MagicMock(spec=ResourceWorkflowStep)
        self.step1.set_status(self.step1.ROOT_STATUS_KEY, 'Error')
        msg = 'Some helpful error message'
        self.step1.set_attribute(self.step1.ATTR_STATUS_MESSAGE, msg)

        ret = ResourceWorkflowView().get_context(self.request, self.session, resource, context, model_db,
                                                 str(self.workflow.id), str(self.step1.id))

        msg_call_args = mock_messages.error.call_args_list
        self.assertEqual(msg, msg_call_args[0][0][1])
        self.assertEqual(self.workflow.id, ret['workflow'].id)
        self.assertEqual(len(self.workflow.steps), len(ret['steps']))
        self.assertEqual(None, ret['previous_step'])
        self.assertEqual(self.step2, ret['next_step'])
        self.assertEqual('my_workspace:generic_workflow_workflow_step', ret['step_url_name'])
        self.assertIn(self.workflow.name, ret['nav_title'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.messages')
    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_context_success_message(self, mock_app, mock_messages, mock_uhar):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        resource = mock.MagicMock()
        context = {}
        model_db = mock.MagicMock(spec=ResourceWorkflowStep)
        self.step1.set_status(self.step1.ROOT_STATUS_KEY, 'Complete')
        msg = 'Some helpful success message'
        self.step1.set_attribute(self.step1.ATTR_STATUS_MESSAGE, msg)

        ret = ResourceWorkflowView().get_context(self.request, self.session, resource, context, model_db,
                                                 str(self.workflow.id), str(self.step1.id))

        msg_call_args = mock_messages.success.call_args_list
        self.assertEqual(msg, msg_call_args[0][0][1])
        self.assertEqual(self.workflow.id, ret['workflow'].id)
        self.assertEqual(len(self.workflow.steps), len(ret['steps']))
        self.assertEqual(None, ret['previous_step'])
        self.assertEqual(self.step2, ret['next_step'])
        self.assertEqual('my_workspace:generic_workflow_workflow_step', ret['step_url_name'])
        self.assertIn(self.workflow.name, ret['nav_title'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.messages')
    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_context_info_message(self, mock_app, mock_messages, mock_uhar):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        resource = mock.MagicMock()
        context = {}
        model_db = mock.MagicMock(spec=ResourceWorkflowStep)
        self.step1.set_status(self.step1.STATUS_WORKING, 'Complete')
        msg = 'Some helpful info message'
        self.step1.set_attribute(self.step1.ATTR_STATUS_MESSAGE, msg)

        ret = ResourceWorkflowView().get_context(self.request, self.session, resource, context, model_db,
                                                 str(self.workflow.id), str(self.step1.id))

        msg_call_args = mock_messages.info.call_args_list
        self.assertEqual(msg, msg_call_args[0][0][1])
        self.assertEqual(self.workflow.id, ret['workflow'].id)
        self.assertEqual(len(self.workflow.steps), len(ret['steps']))
        self.assertEqual(None, ret['previous_step'])
        self.assertEqual(self.step2, ret['next_step'])
        self.assertEqual('my_workspace:generic_workflow_workflow_step', ret['step_url_name'])
        self.assertIn(self.workflow.name, ret['nav_title'])

    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_step_url_name(self, mock_app):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        self.request.path = 'apps/and/such'

        ret = ResourceWorkflowView().get_step_url_name(self.request, self.workflow)

        self.assertEqual('my_workspace:generic_workflow_workflow_step', ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)
    def test_build_step_cards(self, mock_uhar):
        mock_request = mock.MagicMock(spec=HttpRequest)
        self.workflow.steps.append(ResourceWorkflowStep())

        steps = ResourceWorkflowView().build_step_cards(mock_request, self.workflow)

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

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView'
                '.user_has_active_role', return_value=True)
    def test_build_step_cards_no_steps(self, mock_uhar):
        mock_request = mock.MagicMock(spec=HttpRequest)
        workflow = mock.MagicMock(spec=ResourceWorkflow)
        workflow.steps = []

        steps = ResourceWorkflowView().build_step_cards(mock_request, workflow)

        self.assertEqual(workflow.steps, steps)

    # TODO: TEST USER DOES NOT HAVE ACTIVE ROLE

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.reverse')
    @mock.patch('tethys_apps.models.TethysApp')
    def test_save_step_data_with_active_role(self, mock_app, mock_reverse, mock_permission):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        mock_reverse.return_value = './mock_url'
        mock_permission.return_value = None
        resource = mock.MagicMock(spec=Resource)
        self.step1.active_roles = []
        self.request.POST = 'next-submit'

        ret = ResourceWorkflowView().save_step_data(self.request, self.workflow.id, self.step1.id, './back_url',
                                                    resource.id, resource, self.session)

        self.assertIsInstance(ret, HttpResponse)
        self.assertEqual('./mock_url', ret['location'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.reverse')
    @mock.patch('tethys_apps.models.TethysApp')
    def test_save_step_data_without_active_role(self, mock_app, mock_reverse, mock_permission, mock_active_role):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        mock_reverse.return_value = './mock_url'
        mock_permission.return_value = None
        mock_active_role.return_value = False
        resource = mock.MagicMock(spec=Resource)
        self.request.POST = 'prev-submit'

        ret = ResourceWorkflowView().save_step_data(self.request, self.workflow.id, self.step3.id, './back_url',
                                                    resource.id, resource, self.session)

        self.assertIsInstance(ret, HttpResponse)
        self.assertEqual('./mock_url', ret['location'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_user_has_active_role_active(self, mock_gpm, mock_permission):
        mock_gpm.return_value = mock.MagicMock(spec=AppPermissionsManager)
        mock_permission.return_value = True
        self.step1.active_roles = ['has_advanced_user_role']

        ret = ResourceWorkflowView().user_has_active_role(self.request, self.step1)

        self.assertTrue(ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_user_has_active_role_not_active(self, mock_gpm, mock_permission):
        mock_gpm.return_value = mock.MagicMock(spec=AppPermissionsManager)
        mock_permission.return_value = False
        self.workflow.steps[0].active_roles = ['has_advanced_user_role']

        ret = ResourceWorkflowView().user_has_active_role(self.request, self.workflow.steps[0])

        self.assertFalse(ret)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_user_has_active_role_not_defined(self, mock_gpm):
        mock_gpm.return_value = mock.MagicMock(spec=AppPermissionsManager)
        self.workflow.steps[0].active_roles = []

        ret = ResourceWorkflowView().user_has_active_role(self.request, self.workflow.steps[0])

        self.assertTrue(ret)

    def test_validate_step_valid(self):
        was_thrown = False

        try:
            ResourceWorkflowView().validate_step(None, self.session, ResourceWorkflowStep(), None, None)
        except TypeError:
            was_thrown = True

        self.assertFalse(was_thrown)

    def test_validate_step_invalid(self):
        with self.assertRaises(TypeError) as e:
            ResourceWorkflowView().validate_step(None, self.session, InvalidStep(), None, None)
        self.assertEqual(
            'Invalid step type for view: "InvalidStep". Must be one of "ResourceWorkflowStep".',
            str(e.exception))

    def test_on_get(self):
        resource = mock.MagicMock()

        ret = ResourceWorkflowView().on_get(self.request, self.session, resource,
                                            str(self.workflow.id), str(self.step2.id))

        self.assertEqual(None, ret)

    def test_process_step_data_dirty(self):
        self.request.POST = 'submit'
        self.step1.dirty = True

        ret = ResourceWorkflowView().process_step_data(self.request, mock.MagicMock(), self.step1, None,
                                                       self.current_url, self.previous_url, self.next_url)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.previous_url, ret['location'])
        self.assertFalse(self.step1.dirty)

    def test_process_step_data_not_dirty(self):
        self.request.POST = 'next-submit'
        self.step1.dirty = False

        ret = ResourceWorkflowView().process_step_data(self.request, self.session, self.step1, None,
                                                       self.current_url, self.previous_url, self.next_url)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.next_url, ret['location'])
        self.assertFalse(self.step1.dirty)

    def test_navigate_only_complete(self):
        self.request.POST = 'submit'
        self.step1.set_status(self.step1.ROOT_STATUS_KEY, self.step1.STATUS_COMPLETE)

        response = ResourceWorkflowView().navigate_only(self.request, self.step1, self.current_url,
                                                        self.next_url, self.previous_url)

        self.assertEqual(self.previous_url, response['location'])

    # TODO: Test case where there are not roles...
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.messages')
    def test_navigate_only_not_complete(self, mock_messages):
        self.request.POST = 'next-submit'
        self.step1.active_roles = [Roles.ORG_REVIEWER]

        response = ResourceWorkflowView().navigate_only(self.request, self.step1, self.current_url,
                                                        self.next_url, self.previous_url)

        mock_messages.info.assert_called_with(self.request, 'You may not proceed until this step is completed by a '
                                                            'user with one of the following roles: '
                                                            'Organization Reviewer.')
        self.assertEqual(self.current_url, response['location'])

    def test_get_style_for_status(self):
        rwv = ResourceWorkflowView()

        self.assertEqual('success', rwv.get_style_for_status(StatusMixin.STATUS_COMPLETE))
        self.assertEqual('success', rwv.get_style_for_status(StatusMixin.STATUS_APPROVED))
        self.assertEqual('warning', rwv.get_style_for_status(StatusMixin.STATUS_SUBMITTED))
        self.assertEqual('warning', rwv.get_style_for_status(StatusMixin.STATUS_UNDER_REVIEW))
        self.assertEqual('warning', rwv.get_style_for_status(StatusMixin.STATUS_CHANGES_REQUESTED))
        self.assertEqual('warning', rwv.get_style_for_status(StatusMixin.STATUS_WORKING))
        self.assertEqual('danger', rwv.get_style_for_status(StatusMixin.STATUS_ERROR))
        self.assertEqual('danger', rwv.get_style_for_status(StatusMixin.STATUS_FAILED))
        self.assertEqual('danger', rwv.get_style_for_status(StatusMixin.STATUS_REJECTED))
        self.assertEqual('primary', rwv.get_style_for_status('unsupported status'))
