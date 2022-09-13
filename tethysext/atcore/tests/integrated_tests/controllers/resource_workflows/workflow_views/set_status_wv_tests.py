from unittest import mock

from django.http import HttpRequest
from tethysext.atcore.tests.factories.django_user import UserFactory
from django.test import RequestFactory
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.models.resource_workflow_steps import SetStatusRWS
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resource_workflows.workflow_views import SetStatusWV
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SetStatusWVTests(WorkflowViewTestCase):
    current_url = './current'
    previous_url = './previous'
    next_url = './next'

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        self.context = {}

        self.ssrws_no_options = SetStatusRWS(
            name='ssrws_no_options',
            help='No options specified',
            order=1,
        )
        self.ssrws_no_options.set_status(status=self.ssrws_no_options.STATUS_SUBMITTED)

        self.ssrws_three_statuses = SetStatusRWS(
            name='ssrws_three_statuses',
            help='Three statuses',
            order=2,
            options={
                'statuses': [
                    {'status': SetStatusRWS.STATUS_APPROVED,
                     'label': 'Approve'},
                    {'status': SetStatusRWS.STATUS_CHANGES_REQUESTED},
                    {'status': SetStatusRWS.STATUS_REJECTED,
                     'label': None},
                ]
            },
        )
        self.ssrws_three_statuses.set_status(status=self.ssrws_three_statuses.STATUS_APPROVED)
        self.workflow.steps.append(self.ssrws_three_statuses)

        self.ssrws_custom_titles = SetStatusRWS(
            name='ssrws_custom_titles',
            help='help3',
            order=3,
            options={
                'form_title': 'Custom Title',
                'status_label': 'Choose One',
            }
        )
        self.ssrws_custom_titles.set_status(status=self.ssrws_custom_titles.STATUS_REJECTED)
        self.workflow.steps.append(self.ssrws_custom_titles)

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
        uhar_patcher = mock.patch.object(ResourceWorkflowView, 'user_has_active_role')
        self.mock_uhar = uhar_patcher.start()
        uhar_patcher.return_value = True
        self.addCleanup(uhar_patcher.stop)

        # Patch ResourceWorkflowView.process_step_data
        psd_patcher = mock.patch.object(ResourceWorkflowView, 'process_step_data')
        self.mock_psd = psd_patcher.start()
        self.addCleanup(psd_patcher.stop)

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    def test_process_step_options_ssrws_no_options(self, _, __):
        self.workflow.steps.append(self.ssrws_no_options)

        request = self.request_factory.get('/foo/bar/set-status')
        request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_context = {}

        ret = SetStatusWV().process_step_options(
            request=request,
            session=self.session,
            context=mock_context,
            resource=mock_resource,
            current_step=self.ssrws_no_options,
            previous_step=None,
            next_step=None
        )

        expected_context = {
            'read_only': False,
            'form_title': self.ssrws_no_options.name,
            'status_label': SetStatusWV.default_status_label,
            'statuses': [
                {'status': SetStatusRWS.STATUS_COMPLETE,
                 'label': None}
            ],
            'comments': '',
            'status': SetStatusRWS.STATUS_SUBMITTED,
            'status_style': 'warning'
        }
        self.assertIsNone(ret)
        self.assertDictEqual(expected_context, mock_context)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    def test_process_step_options_ssrws_three_statuses(self, _, __):
        request = self.request_factory.get('/foo/bar/set-status')
        request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_context = {}

        ret = SetStatusWV().process_step_options(
            request=request,
            session=self.session,
            context=mock_context,
            resource=mock_resource,
            current_step=self.ssrws_three_statuses,
            previous_step=None,
            next_step=None
        )

        expected_context = {
            'read_only': False,
            'form_title': self.ssrws_three_statuses.name,
            'status_label': SetStatusWV.default_status_label,
            'statuses': [
                {'status': SetStatusRWS.STATUS_APPROVED,
                 'label': 'Approve'},
                {'status': SetStatusRWS.STATUS_CHANGES_REQUESTED},
                {'status': SetStatusRWS.STATUS_REJECTED,
                 'label': None},
            ],
            'comments': '',
            'status': SetStatusRWS.STATUS_APPROVED,
            'status_style': 'success'
        }
        self.assertIsNone(ret)
        self.assertDictEqual(expected_context, mock_context)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    def test_process_step_options_ssrws_custom_titles(self, _, __):
        request = self.request_factory.get('/foo/bar/set-status')
        request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_context = {}

        ret = SetStatusWV().process_step_options(
            request=request,
            session=self.session,
            context=mock_context,
            resource=mock_resource,
            current_step=self.ssrws_custom_titles,
            previous_step=None,
            next_step=None
        )

        expected_context = {
            'read_only': False,
            'form_title': 'Custom Title',
            'status_label': 'Choose One',
            'statuses': [
                {'status': SetStatusRWS.STATUS_COMPLETE,
                 'label': None}
            ],
            'comments': '',
            'status': SetStatusRWS.STATUS_REJECTED,
            'status_style': 'danger'
        }
        self.assertIsNone(ret)
        self.assertDictEqual(expected_context, mock_context)

    def test_process_step_data_ssrws_no_options(self):
        self.workflow.steps.append(self.ssrws_no_options)

        comment = 'This is my comment.'

        data = {
            'comments': comment,
            'status': SetStatusRWS.STATUS_COMPLETE
        }

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/set-status', data=data)
        request.user = self.django_user

        mock_model_db = mock.MagicMock(spec=ModelDatabase)

        ret = SetStatusWV().process_step_data(
            request=request,
            session=self.session,
            step=self.ssrws_no_options,
            model_db=mock_model_db,
            current_url=current_url,
            next_url=next_url,
            previous_url=previous_url
        )

        self.assertEqual(self.mock_psd(), ret)

        step = self.session.query(SetStatusRWS).filter(SetStatusRWS.name == 'ssrws_no_options').one()
        self.assertEqual(SetStatusRWS.STATUS_COMPLETE, step.get_status())
        self.assertEqual(comment, step.get_parameter('comments'))

    def test_process_step_data_no_status_ssrws_no_options(self):
        comment = 'This is my comment.'

        data = {
            'comments': comment,
        }

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/set-status', data=data)
        request.user = self.django_user

        mock_model_db = mock.MagicMock(spec=ModelDatabase)

        with self.assertRaises(ValueError) as cm:
            SetStatusWV().process_step_data(
                request=request,
                session=self.session,
                step=self.ssrws_no_options,
                model_db=mock_model_db,
                current_url=current_url,
                next_url=next_url,
                previous_url=previous_url
            )

        self.assertEqual('The "Status" field is required.', str(cm.exception))

    def test_process_step_data_no_status_ssrws_custom_titles(self):
        comment = 'This is my comment.'

        data = {
            'comments': comment,
        }

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/set-status', data=data)
        request.user = self.django_user

        mock_model_db = mock.MagicMock(spec=ModelDatabase)

        with self.assertRaises(ValueError) as cm:
            SetStatusWV().process_step_data(
                request=request,
                session=self.session,
                step=self.ssrws_custom_titles,
                model_db=mock_model_db,
                current_url=current_url,
                next_url=next_url,
                previous_url=previous_url
            )

        self.assertEqual('The "Choose One" field is required.', str(cm.exception))

    def test_process_step_data_invalid_status(self):
        comment = 'This is my comment.'

        data = {
            'comments': comment,
            'status': 'not a status'
        }

        current_url = '/foo/bar/set-status'
        next_url = '/foo/bar/set-status/next'
        previous_url = '/foo/bar/set-status/previous'
        request = self.request_factory.post('/foo/bar/set-status', data=data)
        request.user = self.django_user

        mock_model_db = mock.MagicMock(spec=ModelDatabase)

        with self.assertRaises(RuntimeError) as cm:
            SetStatusWV().process_step_data(
                request=request,
                session=self.session,
                step=self.ssrws_no_options,
                model_db=mock_model_db,
                current_url=current_url,
                next_url=next_url,
                previous_url=previous_url
            )

        self.assertEqual('Invalid status given: "not a status".', str(cm.exception))
