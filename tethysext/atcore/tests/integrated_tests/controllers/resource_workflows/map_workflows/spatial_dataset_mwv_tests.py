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
from tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws import SpatialDatasetRWS
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialDatasetMwvTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.GET = {'feature_id': 'feature1'}
        self.request.POST = QueryDict('next-submit')
        self.request.method = 'method1'
        self.request.path = 'path'
        self.request.META = {}
        self.resource = Resource()
        self.back_url = './back'
        self.next_url = './next'
        self.current_url = './current'

        self.workflow = ResourceWorkflow()

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

        # self.session.add(self.workflow)
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

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    def test_get_popup_form_no_dataset(self, mock_get_param):
        mock_get_param.return_value = {self.request.GET['feature_id']: None}

        ret = SpatialDatasetMWV().get_popup_form(self.request, self.workflow.id, self.step1.id,
                                                 back_url=self.back_url, resource=self.resource, session=self.session)

        self.assertIsInstance(ret, HttpResponse)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    def test_save_spatial_data_no_active_role(self, mock_user_role, _):
        mock_user_role.return_value = False

        ret = SpatialDatasetMWV().save_spatial_data(self.request, self.workflow.id, self.step1.id,
                                                    back_url=self.back_url, resource=self.resource,
                                                    session=self.session)

        self.assertIsInstance(ret, JsonResponse)
        expected = b'{"success": false, "error": "You do not have permission to save changes on this step."}'
        self.assertEqual(expected, ret.__dict__['_container'][0])

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    def test_save_spatial_data(self, mock_user_role, _):
        mock_user_role.return_value = True

        ret = SpatialDatasetMWV().save_spatial_data(self.request, self.workflow.id, self.step1.id,
                                                    back_url=self.back_url, resource=self.resource,
                                                    session=self.session)

        self.assertIsInstance(ret, JsonResponse)
        self.assertEqual([b'{"success": true}'], ret.__dict__['_container'])

    def test_process_step_data(self):
        model_db = mock.MagicMock(spec=ModelDatabase)

        ret = SpatialDatasetMWV().process_step_data(self.request, self.session, self.step1, model_db, self.current_url,
                                                    self.back_url, self.next_url)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.next_url, ret.url)
