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
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from tethys_apps.models import TethysApp
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.controllers.resource_workflows.mixins import WorkflowViewMixin
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.mixins.results_mixin import ResultsMixin
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.models.controller_metadata import ControllerMetadata
from tethysext.atcore.models.resource_workflow_steps.results_rws import ResultsResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows.resource_workflow_router import ResourceWorkflowRouter
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FakeController:
    def __init__(self, request, resource_id, workflow_id, step_id, back_url, *args, **kwargs):
        self.request = request
        self.resource_id = resource_id
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.back_url = back_url
        self.args = args
        self.kwargs = kwargs


class RaiseStatementError(ResourceWorkflowRouter):
    def get_workflow(self, request=None, workflow_id=None, session=None):
        raise StatementError(None, None, None, None)

    def get_step(self, request=None, step_id=None, session=None):
        raise StatementError(None, None, None, None)


class RaiseNoResultFound(ResourceWorkflowRouter):
    def get_workflow(self, request=None, workflow_id=None, session=None):
        raise NoResultFound()

    def get_step(self, request=None, step_id=None, session=None):
        raise NoResultFound()


class RaiseATCoreException(ResourceWorkflowRouter):
    def get_workflow(self, request=None, workflow_id=None, session=None):
        raise ATCoreException('This is the ATCore exception.')

    def get_step(self, request=None, step_id=None, session=None):
        raise ATCoreException('This is the ATCore exception.')


class ChildResourceWorkflowRouter(ResourceWorkflowRouter):
    back_url = 'back_url'


class ResourceWorkflowRouterTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.result_id = 123456

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.path = 'apps/request/path'

        self.resource = Resource()
        self.session.add(self.resource)

        self.app = mock.MagicMock(spec=TethysApp, package='app_namespace')

        self.workflow = ResourceWorkflow(name='foo')

        self.step1 = ResourceWorkflowStep(
            name='step1',
            help='help1',
            order=1
        )
        self.workflow.steps.append(self.step1)

        self.result_step = ResultsResourceWorkflowStep(
            name='result_step',
            help='Result help',
        )

        self.workflow.steps = [self.result_step]
        self.session.add(self.workflow)
        self.session.commit()

        messages_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.messages')  # noqa: E501
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        redirect_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.redirect')  # noqa: E501
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        reverse_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.reverse')
        self.mock_reverse = reverse_patcher.start()
        self.addCleanup(reverse_patcher.stop)

        reverse_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
        self.mock_mixins_reverse = reverse_mixins_patcher.start()
        self.addCleanup(reverse_mixins_patcher.stop)

        last_result_patcher = mock.patch.object(ResultsMixin, 'get_last_result')  # The method needs to be patched as an object so it is recognized when called from instances of the class
        self.mock_get_last_result = last_result_patcher.start()
        self.mock_get_last_result.return_value = mock.MagicMock(id=self.result_id)
        self.addCleanup(last_result_patcher.stop)

        get_result_patcher = mock.patch.object(ResultsMixin, 'get_result')
        self.mock_get_result = get_result_patcher.start()
        self.mock_get_result.return_value = mock.MagicMock(
            controller=mock.MagicMock(http_methods=['get', 'post', 'delete'])
        )
        self.addCleanup(get_result_patcher.stop)

        get_app_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.get_active_app')
        self.mock_get_mixins_app = get_app_mixins_patcher.start()
        self.mock_get_mixins_app.return_value = self.app
        self.addCleanup(get_app_mixins_patcher.stop)

        get_app_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.get_active_app')  # noqa: E501
        self.mock_get_app = get_app_patcher.start()
        self.mock_get_app.return_value = self.app
        self.addCleanup(get_app_patcher.stop)

        session_patcher = mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
        self.mock_get_session_maker = session_patcher.start()
        self.mock_get_session_maker.return_value = mock.MagicMock
        self.addCleanup(session_patcher.stop)

        get_step_mixins_patcher = mock.patch.object(WorkflowViewMixin, 'get_step')  # noqa: E501
        self.mock_get_step_mixins = get_step_mixins_patcher.start()
        self.mock_get_step_mixins.return_value = self.result_step
        self.addCleanup(get_step_mixins_patcher.stop)

        initiate_meta_patcher = mock.patch.object(ControllerMetadata, 'instantiate')
        self.mock_initiate_meta = initiate_meta_patcher.start()
        self.mock_initiate_meta.return_value = FakeController
        self.addCleanup(initiate_meta_patcher.stop)

        get_workflow_patcher = mock.patch.object(WorkflowViewMixin, 'get_workflow')  # noqa: E501
        self.mock_get_workflow = get_workflow_patcher.start()
        self.mock_get_workflow.return_value = self.workflow
        self.addCleanup(get_workflow_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def test_get_with_step_id(self):
        self.session.delete(self.workflow)
        self.workflow.steps = [self.step1]
        self.session.add(self.workflow)
        self.session.commit()
        self.request.method = 'get'
        controller = ResourceWorkflowRouter.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id,
            step_id=self.step1.id
        )

        self.mock_redirect.assert_called()
        url_name = f'{self.app.package}:generic_workflow_workflow_step_result'
        self.assertEqual(url_name, self.mock_reverse.call_args_list[0][0][0])
        url_kwargs = {
            'resource_id': self.resource.id,
            'workflow_id': self.workflow.id,
            'step_id': self.step1.id,
            'result_id': str(self.result_id)
        }
        self.assertEqual(url_kwargs, self.mock_reverse.call_args_list[0][1]['kwargs'])

    def test_get_last_return(self):
        self.session.delete(self.workflow)
        self.workflow.steps = [self.step1]
        self.session.add(self.workflow)
        self.session.commit()
        self.request.method = 'get'
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id,
            step_id=self.step1.id,
            result_id=self.result_id
        )

        call_args = response._mock_new_parent._mock_call_args_list[0][1]
        self.assertEqual(self.request, call_args['request'])
        self.assertEqual(self.resource.id, call_args['resource_id'])
        self.assertEqual(self.workflow.id, call_args['workflow_id'])
        self.assertEqual(self.step1.id, call_args['step_id'])
        self.assertIn('back_url', call_args)

    def test_get_no_optional_args(self):
        self.request.method = 'get'
        controller = ResourceWorkflowRouter.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        self.mock_redirect.assert_called()
        url_name = f'{self.app.package}:generic_workflow_workflow_step_result'
        self.assertEqual(url_name, self.mock_reverse.call_args_list[0][0][0])
        url_kwargs = {
            'resource_id': self.resource.id,
            'workflow_id': self.workflow.id,
            'step_id': self.result_step.id,
            'result_id': str(self.result_id)
        }
        self.assertEqual(url_kwargs, self.mock_reverse.call_args_list[0][1]['kwargs'])

    def test_get_not_result_step(self):
        self.session.delete(self.workflow)
        self.workflow.steps = [self.step1]
        self.session.add(self.workflow)
        self.session.commit()
        self.request.method = 'get'
        self.mock_get_step_mixins.return_value = self.step1
        controller = ResourceWorkflowRouter.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        self.mock_redirect.assert_called()
        url_name = f'{self.app.package}:generic_workflow_workflow_step'
        self.assertEqual(url_name, self.mock_reverse.call_args_list[0][0][0])
        url_kwargs = {
            'resource_id': self.resource.id,
            'workflow_id': self.workflow.id,
            'step_id': self.step1.id
        }
        self.assertEqual(url_kwargs, self.mock_reverse.call_args_list[0][1]['kwargs'])

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_bad_next_step(self, mock_get_next_step):
        mock_get_next_step.return_value = None, None
        self.request.method = 'get'
        controller = ChildResourceWorkflowRouter.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('Could not identify next step.', msg_warning_args[0][0][1])

    def test_get_bad_result_id(self):
        self.request.method = 'get'
        self.mock_get_last_result.return_value = None
        controller = ResourceWorkflowRouter.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('Could not identify a result.', msg_warning_args[0][0][1])

    def test_get_statement_error(self):
        self.request.method = 'get'
        controller = RaiseStatementError.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic workflow could not be found.', msg_warning_args[0][0][1])

    def test_get_no_result_found(self):
        self.request.method = 'get'
        controller = RaiseNoResultFound.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic workflow could not be found.', msg_warning_args[0][0][1])

    def test_get_atcore_exception(self):
        self.request.method = 'get'
        controller = RaiseATCoreException.as_controller()

        controller(
            request=self.request,
            resource_id=self.resource.id,
            workflow_id=self.workflow.id
        )

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_warning_args[0][0][1])

    def test_post_no_optional_params(self):
        self.session.delete(self.workflow)
        self.workflow.steps = [self.step1]
        self.session.add(self.workflow)
        self.session.commit()
        self.request.method = 'post'
        self.mock_get_step_mixins.return_value = self.step1
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(request=self.request, resource_id=self.resource.id, workflow_id=self.workflow.id,
                              step_id=self.step1.id)

        self.assertEqual(self.request, response.request)
        self.assertEqual(self.resource.id, response.resource_id)
        self.assertEqual(self.workflow.id, response.workflow_id)
        self.assertEqual(self.step1.id, response.step_id)
        self.assertTrue(hasattr(response, 'back_url'))
        self.assertEqual((), response.args)
        self.assertEqual({}, response.kwargs)

    def test_post_with_result_id(self):
        self.request.method = 'post'
        self.mock_get_result.controller.instantiate.return_value = FakeController
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(request=self.request, resource_id=self.resource.id, workflow_id=self.workflow.id,
                              step_id=self.result_step.id, result_id=self.result_id)

        call_args = response._mock_new_parent._mock_call_args[1]
        self.assertEqual(self.request, call_args['request'])
        self.assertEqual(self.resource.id, call_args['resource_id'])
        self.assertEqual(self.workflow.id, call_args['workflow_id'])
        self.assertEqual(self.result_step.id, call_args['step_id'])
        self.assertIn('back_url', call_args)

    def test_route_to_step_controller_statement_error(self):
        RaiseStatementError()._route_to_step_controller(self.request, self.resource.id,
                                                        self.workflow.id, self.step1.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('Invalid step for workflow: generic workflow.', msg_warning_args[0][0][1])

    def test_route_to_step_controller_no_result_found(self):
        RaiseNoResultFound()._route_to_step_controller(self.request, self.resource.id,
                                                       self.workflow.id, self.step1.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('Invalid step for workflow: generic workflow.', msg_warning_args[0][0][1])

    def test_route_to_step_controller_atcore_exception(self):
        RaiseATCoreException()._route_to_step_controller(self.request, self.resource.id,
                                                         self.workflow.id, self.step1.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_warning_args[0][0][1])

    def test_route_to_result_controller_statement_error(self):
        RaiseStatementError()._route_to_result_controller(self.request, self.resource.id,
                                                          self.workflow.id, self.step1.id, self.result_id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('Invalid step for workflow: generic workflow.', msg_warning_args[0][0][1])

    def test_route_to_result_controller_no_result_found(self):
        RaiseNoResultFound()._route_to_result_controller(self.request, self.resource.id,
                                                         self.workflow.id, self.step1.id, self.result_id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('Invalid step for workflow: generic workflow.', msg_warning_args[0][0][1])

    def test_route_to_result_controller_atcore_exception(self):
        RaiseATCoreException()._route_to_result_controller(self.request, self.resource.id,
                                                           self.workflow.id, self.step1.id, self.result_id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_warning_args[0][0][1])

    def test_delete_no_optional_params(self):
        self.session.delete(self.workflow)
        self.workflow.steps = [self.step1]
        self.session.add(self.workflow)
        self.session.commit()
        self.request.method = 'delete'
        self.mock_get_step_mixins.return_value = self.step1
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(request=self.request, resource_id=self.resource.id, workflow_id=self.workflow.id,
                              step_id=self.step1.id)

        self.assertEqual(self.request, response.request)
        self.assertEqual(self.resource.id, response.resource_id)
        self.assertEqual(self.workflow.id, response.workflow_id)
        self.assertEqual(self.step1.id, response.step_id)
        self.assertTrue(hasattr(response, 'back_url'))
        self.assertEqual((), response.args)
        self.assertEqual({}, response.kwargs)

    def test_delete_with_result_id(self):
        self.request.method = 'delete'
        self.mock_get_result.controller.instantiate.return_value = FakeController
        controller = ResourceWorkflowRouter.as_controller()

        response = controller(request=self.request, resource_id=self.resource.id, workflow_id=self.workflow.id,
                              step_id=self.result_step.id, result_id=self.result_id)

        call_args = response._mock_new_parent._mock_call_args[1]
        self.assertEqual(self.request, call_args['request'])
        self.assertEqual(self.resource.id, call_args['resource_id'])
        self.assertEqual(self.workflow.id, call_args['workflow_id'])
        self.assertEqual(self.result_step.id, call_args['step_id'])
        self.assertIn('back_url', call_args)

    def test_route_to_step_controller_invalid_method(self):
        self.request.method = 'do_the_thing'

        try:
            ResourceWorkflowRouter()._route_to_step_controller(self.request, self.resource.id,
                                                               self.workflow.id, self.step1.id)
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual(f'An unexpected error has occurred: Method not allowed ({self.request.method}).', str(e))

    def test_route_to_result_controller_wrong_step_type(self):
        self.mock_get_step_mixins.return_value = self.step1
        try:
            ResourceWorkflowRouter()._route_to_result_controller(self.request, self.resource.id, self.workflow.id,
                                                                 self.step1.id, str(self.result_id))
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual('Step must be a ResultsResourceWorkflowStep.', str(e))

    def test_route_to_result_controller_invalid_method(self):
        self.request.method = 'do_the_thing'

        try:
            ResourceWorkflowRouter()._route_to_result_controller(self.request, self.resource.id, self.workflow.id,
                                                                 self.result_step.id, str(self.result_id))
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual(f'An unexpected error has occurred: Method not allowed ({self.request.method}).', str(e))

    def test_route_to_result_controller_no_result(self):
        self.mock_get_result.return_value = None
        self.request.method = 'get'
        rwr = ResourceWorkflowRouter()
        rwr.back_url = 'back_url'

        ret = rwr._route_to_result_controller(self.request, self.resource.id, self.workflow.id,
                                              self.result_step.id, str(self.result_id))

        msg_error_args = self.mock_messages.error.call_args_list
        self.assertEqual('Result not found.', msg_error_args[0][0][1])
        self.assertEqual(rwr.back_url, ret._mock_new_parent._mock_call_args[0][0])
