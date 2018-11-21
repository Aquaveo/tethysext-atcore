"""
********************************************************************************
* Name: resource_status.py
* Author: nswain
* Created On: September 24, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.app_users.resource_status import ResourceStatus


class ResourceStatusControllerTests(TethysTestCase):

    def setUp(self):
        self.controller = ResourceStatus.as_controller()
        self.resource_id = 'abc123'
        self.user = UserFactory()
        self.request_factory = RequestFactory()

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.ResourceStatus._handle_get')
    def test_get(self, mock_handle_get):
        mock_request = self.request_factory.get('/foo/bar/status/')
        ret = self.controller(mock_request, back_url='/foo/bar')
        mock_handle_get.assert_called_with(mock_request, back_url='/foo/bar')
        self.assertEqual(mock_handle_get(), ret)

    @mock.patch('tethys_apps.decorators.has_permission', return_value=True)
    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.JobsTable')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.render')
    def test_handle_get_without_resource_id(self, mock_render, mock_JobsTable, _):
        mock_request = self.request_factory.get('/foo/bar/status/')
        mock_request.user = self.user
        mock_job1 = mock.MagicMock(extended_properties={})
        mock_job2 = mock.MagicMock(extended_properties={'resource_id': 'def456'})
        mock_job3 = mock.MagicMock(extended_properties={'resource_id': self.resource_id})
        all_jobs = [mock_job1, mock_job2, mock_job3]
        mock_app = mock.MagicMock()
        mock_app.get_job_manager().list_jobs.return_value = all_jobs
        controller = ResourceStatus.as_controller(_app=mock_app)

        ret = controller(mock_request, back_url='/foo/bar')

        mjt_call_args = mock_JobsTable.call_args_list
        self.assertEqual(all_jobs, mjt_call_args[0][1]['jobs'])
        mr_call_args = mock_render.call_args_list
        context = mr_call_args[0][0][2]
        self.assertEqual(mock_JobsTable(), context['jobs_table'])
        self.assertIsNone(context['resource_id'])
        self.assertIsNone(context['resource'])
        self.assertEqual(mock_render(), ret)

    @mock.patch('tethys_apps.decorators.has_permission', return_value=True)
    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.ResourceStatus.get_resource',
                return_value=mock.MagicMock())
    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.JobsTable')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.render')
    def test_handle_get_with_resource_id(self, mock_render, mock_JobsTable, _, __):
        mock_request = self.request_factory.get('/foo/bar/status/?r={}'.format(self.resource_id))
        mock_request.user = self.user
        mock_job1 = mock.MagicMock(extended_properties={})
        mock_job2 = mock.MagicMock(extended_properties={'resource_id': 'def456'})
        mock_job3 = mock.MagicMock(extended_properties={'resource_id': self.resource_id})
        all_jobs = [mock_job1, mock_job2, mock_job3]
        mock_app = mock.MagicMock()
        mock_app.get_job_manager().list_jobs.return_value = all_jobs
        controller = ResourceStatus.as_controller(_app=mock_app)

        ret = controller(mock_request, back_url='/foo/bar')

        mjt_call_args = mock_JobsTable.call_args_list
        self.assertEqual([mock_job3], mjt_call_args[0][1]['jobs'])
        mr_call_args = mock_render.call_args_list
        context = mr_call_args[0][0][2]
        self.assertEqual(mock_JobsTable(), context['jobs_table'])
        self.assertEqual(self.resource_id, context['resource_id'])
        self.assertIsNotNone(context['resource'])
        self.assertEqual(mock_render(), ret)

    @mock.patch('tethys_apps.decorators.has_permission', return_value=True)
    @mock.patch('tethysext.atcore.controllers.app_users.resource_status.ResourceStatus.get_resource')
    def test_handle_get_resource_is_http(self, mock_get_resource, _):
        mock_request = self.request_factory.get('/foo/bar/status/?r={}'.format(self.resource_id))
        mock_request.user = self.user
        mock_app = mock.MagicMock()
        controller = ResourceStatus.as_controller(_app=mock_app)
        redirect_response = mock.MagicMock(spec=HttpResponseRedirect)
        mock_get_resource.return_value = redirect_response

        ret = controller(mock_request, back_url='/foo/bar')

        self.assertEqual(redirect_response, ret)
