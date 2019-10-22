"""
********************************************************************************
* Name: decorators.py
* Author: mlebaron
* Created On: September 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import json
from unittest import mock
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.services.resource_workflows import decorators
from tethysext.atcore.exceptions import ATCoreException
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class WorkflowStepControllerClass(ResourceWorkflowView):
    @decorators.workflow_step_controller()
    def do_the_thing(self, request, session, resource, workflow, step, back_url, *args, **kwargs):
        return {
            'request': request,
            'session': session,
            'resource': resource,
            'workflow': workflow,
            'step': step,
            'back_url': back_url
        }

    @decorators.workflow_step_controller()
    def raise_value_error(self, *args, **kwargs):
        raise ValueError('This is the ValueError')

    @decorators.workflow_step_controller(is_rest_controller=True)
    def raise_value_error_as_rest_controller(self, *args, **kwargs):
        raise ValueError('This is the ValueError')

    @decorators.workflow_step_controller()
    def raise_runtime_error(self, *args, **kwargs):
        raise RuntimeError('This is the Runtime Error')

    @decorators.workflow_step_controller(is_rest_controller=True)
    def raise_runtime_error_as_rest_controller(self, *args, **kwargs):
        raise RuntimeError('This is the Runtime Error')

    @decorators.workflow_step_controller()
    def raise_atcore_exception(self, *args, **kwargs):
        raise ATCoreException('This is the ATCore exception.')

    @decorators.workflow_step_controller(is_rest_controller=True)
    def raise_atcore_exception_as_rest_controller(self, *args, **kwargs):
        raise ATCoreException('This is the ATCore exception.')

    @decorators.workflow_step_controller()
    def raise_statement_error(self, *args, **kwargs):
        raise StatementError('This is the StatementError exception', None, None, None)

    @decorators.workflow_step_controller(is_rest_controller=True)
    def raise_statement_error_as_rest_controller(self, *args, **kwargs):
        raise StatementError('This is the StatementError exception', None, None, None)

    @decorators.workflow_step_controller()
    def raise_no_result_found(self, *args, **kwargs):
        raise NoResultFound('This is the NoResultFound exception.')

    @decorators.workflow_step_controller(is_rest_controller=True)
    def raise_no_result_found_as_rest_controller(self, *args, **kwargs):
        raise NoResultFound('This is the NoResultFound exception.')


class DecoratorsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock()

        self.resource = Resource()
        self.session.add(self.resource)

        self.workflow = ResourceWorkflow()

        self.step = ResourceWorkflowStep(name='name', help='help')
        self.workflow.steps = [self.step]

        self.session.add(self.workflow)
        self.session.commit()

        session_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
        self.mock_get_session_maker = session_patcher.start()
        self.mock_get_session_maker.return_value = mock.MagicMock
        self.addCleanup(session_patcher.stop)

        get_workflow_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')  # noqa: E501
        self.mock_get_workflow = get_workflow_patcher.start()
        self.mock_get_workflow.return_value = self.workflow
        self.addCleanup(get_workflow_patcher.stop)

        get_step_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')  # noqa: E501
        self.mock_get_step = get_step_patcher.start()
        self.mock_get_step.return_value = self.step
        self.addCleanup(get_step_patcher.stop)

        get_resource_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.get_resource')  # noqa: E501
        self.mock_get_resource = get_resource_patcher.start()
        self.mock_get_resource.return_value = self.resource
        self.addCleanup(get_resource_patcher.stop)

        redirect_patcher = mock.patch('tethysext.atcore.services.resource_workflows.decorators.redirect')  # noqa: E501
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        messages_patcher = mock.patch('tethysext.atcore.services.resource_workflows.decorators.messages')  # noqa: E501
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        log_patcher = mock.patch('tethysext.atcore.services.resource_workflows.decorators.log')  # noqa: E501
        self.mock_log = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def test_workflow_step_controller(self):
        ret = WorkflowStepControllerClass().do_the_thing(self.request, self.workflow.id, self.step.id)

        self.assertEqual(self.request, ret['request'])
        self.assertEqual(self.session, self.session)
        self.assertEqual(None, ret['resource'])
        self.assertEqual(self.workflow, ret['workflow'])
        self.assertEqual(self.step, ret['step'])
        self.assertEqual(None, ret['back_url'])

    def test_workflow_step_controller_with_resource_id(self):
        ret = WorkflowStepControllerClass().do_the_thing(self.request, self.workflow.id, self.step.id,
                                                         resource_id=self.resource.id)

        self.assertEqual(self.request, ret['request'])
        self.assertEqual(self.session, self.session)
        self.assertEqual(self.resource, ret['resource'])
        self.assertEqual(self.workflow, ret['workflow'])
        self.assertEqual(self.step, ret['step'])
        self.assertEqual(None, ret['back_url'])

    def test_workflow_step_controller_statement_error(self):
        WorkflowStepControllerClass().raise_statement_error(self.request, self.workflow.id, self.step.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic workflow could not be found.', msg_warning_args[0][0][1])

    def test_workflow_step_controller_statement_error_as_rest_controller(self):
        ret = WorkflowStepControllerClass().raise_statement_error_as_rest_controller(self.request, self.workflow.id,
                                                                                     self.step.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic workflow could not be found.', msg_warning_args[0][0][1])
        ret_dict = json.loads(ret._container[0].decode("utf-8"))
        self.assertFalse(ret_dict['success'])
        self.assertEqual('This is the StatementError exception', ret_dict['error'])

    def test_workflow_step_controller_no_result_found(self):
        WorkflowStepControllerClass().raise_no_result_found(self.request, self.workflow.id, self.step.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic workflow could not be found.', msg_warning_args[0][0][1])

    def test_workflow_step_controller_no_result_found_as_rest_controller(self):
        ret = WorkflowStepControllerClass().raise_no_result_found_as_rest_controller(self.request, self.workflow.id,
                                                                                     self.step.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic workflow could not be found.', msg_warning_args[0][0][1])
        ret_dict = json.loads(ret._container[0].decode("utf-8"))
        self.assertFalse(ret_dict['success'])
        self.assertEqual('This is the NoResultFound exception.', ret_dict['error'])

    def test_workflow_step_controller_atcore_exception(self):
        WorkflowStepControllerClass().raise_atcore_exception(self.request, self.workflow.id, self.step.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_warning_args[0][0][1])

    def test_workflow_step_controller_atcore_exception_as_rest_controller(self):
        ret = WorkflowStepControllerClass().raise_atcore_exception_as_rest_controller(self.request, self.workflow.id,
                                                                                      self.step.id)

        msg_warning_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_warning_args[0][0][1])
        ret_dict = json.loads(ret._container[0].decode("utf-8"))
        self.assertFalse(ret_dict['success'])
        self.assertEqual('This is the ATCore exception.', ret_dict['error'])

    @mock.patch('tethysext.atcore.controllers.resource_view.ResourceView.get')
    def test_workflow_step_controller_value_error(self, _):
        WorkflowStepControllerClass().raise_value_error(self.request, self.workflow.id, self.step.id)

        self.assertEqual('This is the ValueError', self.step.get_attribute(self.step.ATTR_STATUS_MESSAGE))
        self.assertEqual('Error', self.step.get_status(self.step.ROOT_STATUS_KEY))

    @mock.patch('tethysext.atcore.controllers.resource_view.ResourceView.get')
    def test_workflow_step_controller_value_error_as_rest_controller(self, _):
        ret = WorkflowStepControllerClass().raise_value_error_as_rest_controller(self.request, self.workflow.id,
                                                                                 self.step.id)

        self.assertEqual('This is the ValueError', self.step.get_attribute(self.step.ATTR_STATUS_MESSAGE))
        self.assertEqual('Error', self.step.get_status(self.step.ROOT_STATUS_KEY))
        ret_dict = json.loads(ret._container[0].decode("utf-8"))
        self.assertFalse(ret_dict['success'])
        self.assertEqual('This is the ValueError', ret_dict['error'])

    @mock.patch('tethysext.atcore.controllers.resource_view.ResourceView.get')
    def test_workflow_step_controller_runtime_error(self, _):
        WorkflowStepControllerClass().raise_runtime_error(self.request, self.workflow.id, self.step.id)

        self.assertEqual('Error', self.step.get_status(self.step.ROOT_STATUS_KEY))
        msg_error_args = self.mock_messages.error.call_args_list
        self.assertEqual("We're sorry, an unexpected error has occurred.", msg_error_args[0][0][1])
        self.assertEqual('This is the Runtime Error', str(self.mock_log.exception.call_args_list[0][0][0]))

    @mock.patch('tethysext.atcore.controllers.resource_view.ResourceView.get')
    def test_workflow_step_controller_runtime_error_as_rest_controller(self, _):
        ret = WorkflowStepControllerClass().raise_runtime_error_as_rest_controller(self.request, self.workflow.id,
                                                                                   self.step.id)

        self.assertEqual('Error', self.step.get_status(self.step.ROOT_STATUS_KEY))
        msg_error_args = self.mock_messages.error.call_args_list
        self.assertEqual("We're sorry, an unexpected error has occurred.", msg_error_args[0][0][1])
        self.assertEqual('This is the Runtime Error', str(self.mock_log.exception.call_args_list[0][0][0]))
        ret_dict = json.loads(ret._container[0].decode("utf-8"))
        self.assertFalse(ret_dict['success'])
        self.assertEqual('This is the Runtime Error', ret_dict['error'])
