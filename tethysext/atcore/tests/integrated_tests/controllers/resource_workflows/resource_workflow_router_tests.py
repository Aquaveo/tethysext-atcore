"""
********************************************************************************
* Name: resource_workflow_router_tests.py
* Author: mlebaron
* Created On: September 12, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from tethys_apps.models import TethysApp
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.models.resource_workflow_steps.results_rws import ResultsResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows.resource_workflow_router import ResourceWorkflowRouter
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowRouterTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.result_id = 123456

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.path = 'apps/request/path'

        self.resource = Resource()
        self.session.add(self.resource)

        self.app = mock.MagicMock(spec=TethysApp, namespace='app_namespace')

        self.workflow = ResourceWorkflow(name='foo')

        self.step1 = ResourceWorkflowStep(
            name='step1',
            help='help1',
            order=1
        )
        self.workflow.steps.append(self.step1)

        self.step2 = ResourceWorkflowStep(
            name='step2',
            help='help2',
            order=2
        )
        self.workflow.steps.append(self.step2)

        self.result_step = ResultsResourceWorkflowStep(
            name='result_step',
            help='Result help',
        )

        # self.session.add(self.workflow)

        # self.session.commit()

        messages_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.messages')
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        redirect_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.redirect')
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        reverse_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.reverse')
        self.mock_reverse = reverse_patcher.start()
        self.addCleanup(reverse_patcher.stop)

        reverse_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
        self.mock_mixins_reverse = reverse_mixins_patcher.start()
        self.addCleanup(reverse_mixins_patcher.stop)

        last_result_patcher = mock.patch('tethysext.atcore.mixins.results_mixin.ResultsMixin.get_last_result')
        self.mock_get_last_result = last_result_patcher.start()
        self.addCleanup(last_result_patcher.stop)

        get_result_patcher = mock.patch('tethysext.atcore.mixins.results_mixin.ResultsMixin.get_result')
        self.mock_get_result = get_result_patcher.start()
        self.mock_get_result.return_value = mock.MagicMock(
            controller=mock.MagicMock(http_methods=['get', 'post', 'delete'])
        )
        self.addCleanup(get_result_patcher.stop)

        get_app_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.get_active_app')
        self.mock_get_mixins_app = get_app_mixins_patcher.start()
        self.mock_get_mixins_app.return_value = self.app
        self.addCleanup(get_app_mixins_patcher.stop)

        get_app_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.get_active_app')
        self.mock_get_app = get_app_patcher.start()
        self.mock_get_app.return_value = self.app
        self.addCleanup(get_app_patcher.stop)

        session_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
        self.mock_get_session_maker = session_patcher.start()
        self.mock_get_session_maker.return_value = mock.MagicMock
        self.addCleanup(session_patcher.stop)

        get_step_mixins_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
        self.mock_get_step_mixins = get_step_mixins_patcher.start()
        self.addCleanup(get_step_mixins_patcher.stop)

    def tearDown(self):
        super().tearDown()

    # @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')
    # def test_get_no_step_id(self, mock_get_workflow):
    #     mock_get_workflow.return_value = self.workflow
    #
    #     self.workflow.steps = []
    #     self.request.method = 'get'
    #     controller = ResourceWorkflowRouter.as_controller()
    #
    #     response = controller(
    #         request=self.request,
    #         resource_id=self.resource.id,
    #         workflow_id=self.workflow.id
    #     )
    #
    #     msg_call_args = self.mock_messages.warning.call_args_list
    #     self.assertEqual('Could not identify next step.', msg_call_args[0][0][1])
    #     self.mock_redirect.assert_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')
    def test_get_no_optional_args(self, mock_get_workflow):
        mock_get_workflow.return_value = self.workflow
        self.mock_get_last_result.return_value = mock.MagicMock(id=self.result_id)

        self.request.method = 'get'
        self.workflow.steps = [self.result_step]
        self.session.add(self.workflow)
        self.session.commit()
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        self.mock_redirect.assert_called()
        url_name = f'{self.app.namespace}:generic_workflow_workflow_step_result'
        self.assertEqual(url_name, self.mock_reverse.call_args_list[0][0][0])
        url_kwargs = {
            'resource_id': self.resource.id,
            'workflow_id': self.workflow.id,
            'step_id': self.result_step.id,
            'result_id': str(self.result_id)
        }
        self.assertEqual(url_kwargs, self.mock_reverse.call_args_list[0][1]['kwargs'])

    # def test_post_no_optional_params(self):
    #     self.request.method = 'post'
    #     self.workflow.steps = [self.step1]
    #     self.session.add(self.workflow)
    #     self.session.commit()
    #     controller = ResourceWorkflowRouter.as_controller()
    #
    #     response = controller(request=self.request, resource_id=self.resource.id, workflow_id=self.workflow.id,
    #                           step_id=self.step1.id)

    def test_post_with_result_id(self):
        self.mock_get_step_mixins.return_value = self.result_step
        self.request.method = 'post'
        self.workflow.steps = [self.result_step]
        self.session.add(self.workflow)
        self.session.commit()
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(request=self.request, resource_id=self.resource.id, workflow_id=self.workflow.id,
                              step_id=self.result_step.id, result_id=self.result_id)

        breakpoint()
        controller_call_args = response._mock_new_parent.call_args_list[0]
        self.assertIn('back_url', controller_call_args)
        self.assertEqual(self.request, controller_call_args['request'])
