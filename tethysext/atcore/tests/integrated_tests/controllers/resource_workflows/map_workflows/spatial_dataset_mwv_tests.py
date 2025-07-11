"""
********************************************************************************
* Name: spatial_dataset_mwv_tests.py
* Author: mlebaron
* Created On: August 15, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
import pandas as pd
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse, QueryDict
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_dataset_mwv import SpatialDatasetMWV
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws import SpatialDatasetRWS
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialDatasetMwvTests(WorkflowViewTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.GET = {'feature_id': 'feature1'}
        self.request.POST = QueryDict('next-submit')
        self.request.method = 'method1'
        self.request.path = 'path'
        self.request.META = {}
        self.request.user = mock.MagicMock(is_authenticated=True, is_active=True)
        self.back_url = './back'
        self.next_url = './next'
        self.current_url = './current'

        self.step1 = SpatialDatasetRWS(
            geoserver_name='geo_server',
            map_manager=mock.MagicMock(),
            spatial_manager=mock.MagicMock(),
            name='name1',
            help='help1',
            order=1,
            options={
                'max_rows': 1000,
                'template_dataset': pd.DataFrame(columns=['Time (min)']),
                'column': []
            }
        )
        self.workflow.steps.append(self.step1)

        self.session.commit()

        step_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
        self.mock_get_step = step_patcher.start()
        self.addCleanup(step_patcher.stop)
        self.mock_get_step.return_value = self.step1

        workflow_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')  # noqa: E501
        self.mock_get_workflow = workflow_patcher.start()
        self.addCleanup(workflow_patcher.stop)
        self.mock_get_workflow.return_value = self.workflow

    def tearDown(self):
        super().tearDown()

    @mock.patch.object(SpatialDatasetMWV, 'get_step')
    @mock.patch.object(SpatialDatasetMWV, 'get_workflow')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    def test_get_popup_form_no_dataset(self, mock_get_param, mock_get_workflow, mock_get_step):
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = self.step1
        mock_get_param.return_value = {self.request.GET['feature_id']: None}

        ret = SpatialDatasetMWV().get_popup_form(self.request, self.workflow.id, self.step1.id,
                                                 back_url=self.back_url, resource=self.resource, session=self.session)

        self.assertIsInstance(ret, HttpResponse)

    @mock.patch.object(ResourceWorkflow, 'is_locked_for_request_user', return_value=False)
    @mock.patch.object(Resource, 'is_locked_for_request_user', return_value=False)
    @mock.patch.object(SpatialDatasetMWV, 'get_step')
    @mock.patch.object(SpatialDatasetMWV, 'get_workflow')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role')
    def test_save_spatial_data_no_active_role(self, mock_user_role, mock_get_workflow, mock_get_step, _, __):
        mock_user_role.return_value = False
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = self.step1

        ret = SpatialDatasetMWV().save_spatial_data(self.request, self.workflow.id, self.step1.id,
                                                    back_url=self.back_url, resource=self.resource,
                                                    session=self.session)

        self.assertIsInstance(ret, JsonResponse)
        expected = b'{"success": false, "error": "You do not have permission to save changes on this step."}'
        self.assertEqual(expected, ret.__dict__['_container'][0])

    @mock.patch.object(ResourceWorkflowView, 'is_read_only', return_value=False)
    @mock.patch.object(SpatialDatasetMWV, 'get_step')
    @mock.patch.object(SpatialDatasetMWV, 'get_workflow')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role')
    def test_save_spatial_data(self, mock_user_role, mock_get_workflow, mock_get_step, _):
        mock_user_role.return_value = True
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = self.step1

        ret = SpatialDatasetMWV().save_spatial_data(self.request, self.workflow.id, self.step1.id,
                                                    back_url=self.back_url, resource=self.resource,
                                                    session=self.session)

        self.assertIsInstance(ret, JsonResponse)
        self.assertEqual([b'{"success": true}'], ret.__dict__['_container'])

    @mock.patch.object(ResourceWorkflowView, 'is_read_only', return_value=False)
    @mock.patch.object(SpatialDatasetMWV, 'get_step')
    @mock.patch.object(SpatialDatasetMWV, 'get_workflow')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role')
    def test_save_spatial_data_optional_columns(self, mock_user_role, mock_get_workflow, mock_get_step, _):
        optional_step1 = SpatialDatasetRWS(
            geoserver_name='geo_server',
            map_manager=mock.MagicMock(),
            spatial_manager=mock.MagicMock(),
            name='name1_optional',
            help='help1_optional',
            order=1,
            options={
                'max_rows': 1000,
                'template_dataset': pd.DataFrame(columns=['Time (min)', 'Optional']),
                'column': [],
                'optional_columns': ['Optional'],
            }
        )
        mock_user_role.return_value = True
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = optional_step1

        ret = SpatialDatasetMWV().save_spatial_data(self.request, self.workflow.id, optional_step1.id,
                                                    back_url=self.back_url, resource=self.resource,
                                                    session=self.session)

        self.assertIsInstance(ret, JsonResponse)
        self.assertEqual([b'{"success": true}'], ret.__dict__['_container'])

    @mock.patch.object(ResourceWorkflowView, 'is_read_only', return_value=False)
    def test_process_step_data(self, _):
        resource = mock.MagicMock(spec=ModelDatabase)

        ret = SpatialDatasetMWV().process_step_data(self.request, self.session, self.step1, resource, self.current_url,
                                                    self.back_url, self.next_url)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.next_url, ret.url)

    @mock.patch.object(ResourceWorkflowView, 'is_read_only', return_value=False)
    @mock.patch.object(SpatialDatasetMWV, 'get_step')
    @mock.patch.object(SpatialDatasetMWV, 'get_workflow')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    def test_option_callbacks(self, mock_get_param, mock_user_role, mock_get_workflow, mock_get_step, _):
        def _dataset_callback(_):
            return pd.DataFrame(columns=['Time (min)', 'Discharge (cfs)'])

        def _columns_callback(_):
            return ('Time (min)', 'Discharge (cfs)'),

        optional_step1 = SpatialDatasetRWS(
            geoserver_name='geo_server',
            map_manager=mock.MagicMock(),
            spatial_manager=mock.MagicMock(),
            name='name1_optional',
            help='help1_optional',
            order=1,
            options={
                'max_rows': 1000,
                'template_dataset': _dataset_callback,
                'column': [],
                'plot_columns': _columns_callback,
                'optional_columns': _columns_callback,
                'read_only_columns': _columns_callback,
            }
        )
        mock_user_role.return_value = True
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = optional_step1
        mock_get_param.return_value = {self.request.GET['feature_id']: None}

        ret = SpatialDatasetMWV().get_popup_form(self.request, self.workflow.id, optional_step1.id,
                                                 back_url=self.back_url, resource=self.resource, session=self.session)

        self.assertIsInstance(ret, HttpResponse)
        search_bytes = b"data-plot-columns"
        self.assertIn(search_bytes, ret.content)
        search_bytes = b"[[&quot;Time (min)&quot;, &quot;Discharge (cfs)&quot;]]"
        self.assertIn(search_bytes, ret.content)

        ret = SpatialDatasetMWV().save_spatial_data(self.request, self.workflow.id, optional_step1.id,
                                                    back_url=self.back_url, resource=self.resource,
                                                    session=self.session)

        self.assertIsInstance(ret, JsonResponse)
        self.assertEqual([b'{"success": true}'], ret.__dict__['_container'])
