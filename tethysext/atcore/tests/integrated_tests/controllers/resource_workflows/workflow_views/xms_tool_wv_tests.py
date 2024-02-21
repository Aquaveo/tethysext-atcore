from unittest import mock

import param
from django.http import HttpRequest
from typing import Any, Optional
from dataclasses import dataclass

from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.tests.factories.django_user import UserFactory
from django.test import RequestFactory
from tethysext.atcore.services.app_users.roles import Roles
# from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.models.resource_workflow_steps import XMSToolRWS
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resource_workflows.workflow_views import generate_django_form_xmstool, XMSToolWV


@dataclass
class Parameter:
    """Argument data for UI."""
    type: str
    label: str
    default: Any
    precedence: int
    objects: Optional[list[str]] = None
    doc: Optional[str] = None
    default_suffix: str = None
    _value: Any = None
    value: Any = None
    table_definition: Any = None


class TestResource:
    def __init__(self):
        self.foo = 'bar'

    # def datasets(self):
        # return ['abc', '123']


class TestTool(param.Parameterized):
    int_value = param.Integer()
    string_value = param.String()

    def __init__(self, request=None, session=None, resource=None):
        self.request = request
        self.session = session
        self.resource = resource

    def initial_arguments(self):
        arguments = []

        argument1 = mock.MagicMock(name='name', description='name description', type='integer', value=1,
                                   io_direction=1, precedence=1)
        argument1.name = 'name'
        argument1.io_direction = 1
        argument1.get_param.return_value = Parameter(type='Integer', label='name label', default=1, precedence=1,
                                                     objects=None, doc='Arg 1', default_suffix=None, _value=None,
                                                     table_definition=None)
        arguments.append(argument1)

        argument2 = mock.MagicMock(name='foo', description='foo description', type='float', value=2.0,
                                   io_direction=1, precedence=1)
        argument2.name = 'foo'
        argument2.io_direction = 2
        argument2.get_param.return_value = Parameter(type='Number', label='foo label', default=2.0, precedence=2,
                                                     objects=None, doc='Arg 2', default_suffix=None, _value=None,
                                                     table_definition=None)
        arguments.append(argument2)

        argument3 = mock.MagicMock(name='bar', description='bar description', type='string', value='3',
                                   io_direction=1, precedence=3)
        argument3.name = 'bar'
        argument3.io_direction = 1
        argument3.objects = ['a', 'b', 'c']
        argument3.get_param.return_value = Parameter(type='String', label='bar label', default='3', precedence=3,
                                                     objects=None, doc='Arg 3', default_suffix=None, _value=None,
                                                     table_definition=None)
        arguments.append(argument3)

        return arguments


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class XmsToolWVTests(WorkflowViewTestCase):
    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        # xms_tool_class = mock.MagicMock()

        self.context = {}

        self.test_basic_tool = TestTool()
        form_values = {
            'name': {'name': 1},
            'foo': {'foo': 2.0},
            'bar': {'bar': '3'},
        }
        self.test_basic_form_from_param = generate_django_form_xmstool(self.test_basic_tool, form_values)
        self.xrws = XMSToolRWS(
            name='xrws',
            help='basic xmstool input step',
            order=1,
            options={
                'xmstool_class': 'tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.'
                                 'workflow_views.xms_tool_wv_tests.TestTool',
            }
        )

        self.workflow.steps.append(self.xrws)

        self.django_user = UserFactory()
        self.django_user.is_staff = True
        self.django_user.is_superuser = True
        self.django_user.save()

        self.app_user = AppUser(
            username=self.django_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )

        self.request.user = self.app_user

        self.session.add(self.workflow)
        self.session.add(self.app_user)
        self.session.commit()
        self.request_factory = RequestFactory()

        # Patch ResourceWorkflowView.user_has_active_role
        uhar_patcher = mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=True)
        self.mock_uhar = uhar_patcher.start()
        self.addCleanup(uhar_patcher.stop)

        # Patch ResourceWorkflowView.process_step_data
        psd_patcher = mock.patch.object(ResourceWorkflowView, 'process_step_data')
        self.mock_psd = psd_patcher.start()
        self.addCleanup(psd_patcher.stop)

    def tearDown(self):
        super().tearDown()

    @mock.patch.object(ResourceWorkflow, 'is_locked_for_request_user', return_value=False)
    @mock.patch.object(Resource, 'is_locked_for_request_user', return_value=False)
    def test_process_step_options_basic(self, _, __):
        request = self.request_factory.get('/foo/bar/form-input')
        request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_context = {}

        ret = XMSToolWV().process_step_options(
            request=request,
            session=self.session,
            context=mock_context,
            resource=mock_resource,
            current_step=self.xrws,
            previous_step=None,
            next_step=None
        )

        self.assertIsNone(ret)
        self.assertIn('form', mock_context)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_views.xms_tool_wv.generate_django_form_xmstool')  # noqa: E501
    def test_process_step_data_basic(self, mock_gen_form):
        data = {
            'param-form-integer_val': '1',
            'param-form-float_val': '2.0',
            'param-form-string_val': '3',
        }
        mock_gen_form()().is_valid.return_value = True
        mock_gen_form()().cleaned_data = data
        mock_session = mock.MagicMock()

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/form-input', data=data)
        request.user = self.django_user

        mock_resource = mock.MagicMock()

        ret = XMSToolWV().process_step_data(
            request=request,
            session=mock_session,
            step=self.xrws,
            resource=mock_resource,
            current_url=current_url,
            next_url=next_url,
            previous_url=previous_url
        )

        self.assertEqual(self.mock_psd(), ret)
        step = self.session.query(XMSToolRWS).filter(XMSToolRWS.name == 'xrws').one()
        self.assertEqual({'value': {'integer_val': '1', 'float_val': '2.0', 'string_val': '3'}},
                         step.get_parameter('form-values'))

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_views.xms_tool_wv.generate_django_form_xmstool')  # noqa: E501
    def test_process_step_data_assert_is_valid(self, mock_gen_form):
        data = {
            'param-form-integer_val': '1',
            'param-form-float_val': '2.0',
            'param-form-string_val': 'string',
        }
        mock_gen_form()().is_valid.return_value = False
        mock_session = mock.MagicMock()

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/form-input', data=data)
        request.user = self.django_user

        mock_resource = mock.MagicMock()

        with self.assertRaises(RuntimeError) as cm:
            _ = XMSToolWV().process_step_data(
                request=request,
                session=mock_session,
                step=self.xrws,
                resource=mock_resource,
                current_url=current_url,
                next_url=next_url,
                previous_url=previous_url
            )
        self.assertEqual('form is invalid', str(cm.exception))

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_views.xms_tool_wv.generate_django_form_xmstool')  # noqa: E501
    def test_process_step_data_assert_param_data(self, mock_gen_form):
        data = {
            'param-form-integer_val': '1',
            'param-form-float_val': '2.0',
            'param-form-string_val': 'string',
        }
        mock_gen_form()().is_valid.return_value = True
        mock_gen_form()().cleaned_data.__getitem__.side_effect = ValueError('foo_cd')
        mock_session = mock.MagicMock()

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/form-input', data=data)
        request.user = self.django_user

        mock_resource = mock.MagicMock()

        with self.assertRaises(RuntimeError) as cm:
            _ = XMSToolWV().process_step_data(
                request=request,
                session=mock_session,
                step=self.xrws,
                resource=mock_resource,
                current_url=current_url,
                next_url=next_url,
                previous_url=previous_url
            )
        self.assertEqual('error setting param data: foo_cd', str(cm.exception))

    def test_arg_mapping(self):
        mock_setup_func = mock.MagicMock()
        mock_setup_func.return_value = {
            'name': Parameter(type='Integer', label='name "description"', default=3, precedence=1,
                              objects=None, doc='Arg 1', default_suffix=None, _value=None,
                              table_definition=None),
            'foo': Parameter(type='Number', label='foo label2', default=4.4, precedence=2,
                             objects=None, doc='Arg 2', default_suffix=None, _value=None,
                             table_definition=None),
            'bar': Parameter(type='ObjectSelector', label='"bar label"3', default='--None--',
                             precedence=3, objects=[], doc='Arg 3', default_suffix=None,
                             _value=None, table_definition=None),
        }
        mock_dataset = mock.MagicMock()
        mock_dataset.dataset_type = 'ObjectSelector'
        regex_base_description = 'choice description'
        mock_dataset.description = f'"{regex_base_description}" plus extra for filtering out'
        mock_dataset.objects = ['a', 'b', 'c']
        mock_dataset2 = mock.MagicMock()
        mock_dataset2.dataset_type = 'ObjectSelector'
        mock_dataset2.description = 'ds2 description'
        mock_dataset.objects = ['d']
        mock_resource = mock.MagicMock()
        mock_resource.datasets = [mock_dataset, mock_dataset2]

        xmstool_class = TestTool()
        arg_mapping = {
            'bar': {
                'resource_attr': 'datasets',
                'filter_attr': 'dataset_type',
                'valid_values': ['ObjectSelector'],
                'name_attr': 'description',
                'name_attr_regex': r'"(.*?[^\\])"',
            },
        }

        form = generate_django_form_xmstool(xmstool_class, {}, resource=mock_resource,
                                            arg_mapping=arg_mapping, setup_func=mock_setup_func)

        self.assertTrue('name' in form.base_fields)
        self.assertTrue('foo' in form.base_fields)
        self.assertTrue('bar' in form.base_fields)
        self.assertEqual(len(form.base_fields['bar'].choices), 2)
        self.assertEqual(len(form.base_fields['bar'].choices[0]), 2)
        self.assertEqual(len(form.base_fields['bar'].choices[1]), 2)
        self.assertEqual(regex_base_description, form.base_fields['bar'].choices[0][1])
        self.assertEqual(mock_dataset2.description, form.base_fields['bar'].choices[1][1])
