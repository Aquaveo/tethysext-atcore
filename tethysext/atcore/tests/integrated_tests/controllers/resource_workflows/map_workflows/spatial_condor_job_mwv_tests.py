"""
********************************************************************************
* Name: spatial_condor_job_mwv_tests.py
* Author: mlebaron
* Created On: August 16, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv import SpatialCondorJobMWV
from tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws import SpatialDatasetRWS
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialCondorJobMwvTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.map_view = mock.MagicMock(spec=MapView)
        self.map_view.layers = []
        self.context = {
            'map_view': self.map_view,
            'layer_groups': []
        }
        self.resource = mock.MagicMock(spec=Resource)

        self.workflow = ResourceWorkflow()

        self.step = SpatialDatasetRWS(
            geoserver_name='geo_server',
            map_manager=mock.MagicMock(),
            spatial_manager=mock.MagicMock(),
            name='name1',
            help='help1',
            order=1,
            options={}
        )
        self.workflow.steps.append(self.step)

        self.session.commit()

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_process_step_options(self, mock_get_managers, mock_user_role):
        mock_get_managers.return_value = None, self.map_view
        mock_user_role.return_value = True

        SpatialCondorJobMWV().process_step_options(self.request, self.session, self.context, self.resource, self.step,
                                                   None, None)

        self.assertIn('map_view', self.context)
        self.assertIn('layer_groups', self.context)
        self.assertIn('can_run_workflows', self.context)

    # def test_on_get_step_pending(self):
    #     ret = SpatialCondorJobMWV().on_get_step(self.request, self.session, self.resource, self.workflow, self.step,
    #                                             None, None)
