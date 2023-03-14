from unittest import mock

import param
from django.http import HttpRequest
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.tests.factories.django_user import UserFactory
from django.test import RequestFactory
from tethysext.atcore.services.app_users.roles import Roles
# from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.models.resource_workflow_steps import FormInputRWS
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resource_workflows.workflow_views import FormInputWV
from tethysext.atcore.forms.widgets.param_widgets import generate_django_form


class TestParam(param.Parameterized):
    int_value = param.Integer()
    string_value = param.String()


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FormInputWVTests(WorkflowViewTestCase):
    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        self.context = {}

        self.test_basic_param = TestParam()
        self.test_basic_form_from_param = generate_django_form(self.test_basic_param)
        self.firws = FormInputRWS(
            name='firws',
            help='basic form input step',
            order=1,
            options={
                'param_class': 'tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.'
                               'workflow_views.form_input_wv_tests.TestParam'
            }
        )

        self.workflow.steps.append(self.firws)

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

        ret = FormInputWV().process_step_options(
            request=request,
            session=self.session,
            context=mock_context,
            resource=mock_resource,
            current_step=self.firws,
            previous_step=None,
            next_step=None
        )

        self.assertIsNone(ret)
        self.assertIn('form', mock_context)

    def test_process_step_data_ssrws_basic(self):
        pass
        # data = {
        #     'param-form-integer_val': '1',
        #     'param-form-string_val': 'string',
        # }
        #
        # current_url = '/foo/bar/set-status'
        # next_url = '/foo/bar/set-status/next'
        # previous_url = '/foo/bar/set-status/previous'
        # request = self.request_factory.post('/foo/bar/form-input', data=data)
        # request.user = self.django_user
        #
        # mock_resource = mock.MagicMock()
        #
        # ret = FormInputWV().process_step_data(
        #     request=request,
        #     session=self.session,
        #     step=self.firws,
        #     resource=mock_resource,
        #     current_url=current_url,
        #     next_url=next_url,
        #     previous_url=previous_url
        # )
        #
        # self.assertEqual(self.mock_psd(), ret)
        #
        # step = self.session.query(FormInputRWS).filter(FormInputRWS.name == 'firws').one()
        # self.assertEqual({'integer_val': '1', 'string_val': 'string'}, step.get_parameter('form-values'))
