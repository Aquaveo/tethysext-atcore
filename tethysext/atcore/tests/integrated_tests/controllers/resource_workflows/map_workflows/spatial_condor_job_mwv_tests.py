"""
********************************************************************************
* Name: spatial_condor_job_mwv_tests.py
* Author: mlebaron
* Created On: August 16, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest, HttpResponseRedirect
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv import SpatialCondorJobMWV
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


class SpatialCondorJobMwvTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.GET = {}
        self.request.POST = {}
        self.request.path = './path'
        self.request.method = 'POST'
        self.map_view = mock.MagicMock(spec=MapView)
        self.map_view.layers = []
        self.context = {
            'map_view': self.map_view,
            'layer_groups': []
        }
        self.resource = mock.MagicMock(spec=Resource)
        self.model_db = mock.MagicMock(spec=ModelDatabase)
        self.current_url = './current'
        self.next_url = './next'
        self.prev_url = './prev'

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

        message_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv.messages')  # noqa: E501
        self.mock_message = message_patcher.start()
        self.addCleanup(message_patcher.stop)

        get_step_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')  # noqa: E501
        self.mock_get_step = get_step_patcher.start()
        self.addCleanup(get_step_patcher.stop)
        self.mock_get_step.return_value = self.step

        active_role_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
        self.mock_active_role = active_role_patcher.start()
        self.addCleanup(active_role_patcher.stop)
        self.mock_active_role.return_value = True

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_process_step_options(self, mock_get_managers):
        mock_get_managers.return_value = None, self.map_view

        SpatialCondorJobMWV().process_step_options(self.request, self.session, self.context, self.resource, self.step,
                                                   None, None)

        self.assertIn('map_view', self.context)
        self.assertIn('layer_groups', self.context)
        self.assertIn('can_run_workflows', self.context)

    def test_on_get_step_pending(self):
        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_PENDING)

        ret = SpatialCondorJobMWV().on_get_step(self.request, self.session, self.resource, self.workflow, self.step,
                                                None, None)

        self.assertEqual(None, ret)

    def test_process_step_data_not_next(self):
        self.request.POST = {}

        ret = SpatialCondorJobMWV().process_step_data(self.request, self.session, self.step, self.model_db,
                                                      self.current_url, self.prev_url, self.next_url)

        self.assertEqual(self.prev_url, ret.url)
        self.assertEqual(('Location', self.prev_url), ret.__dict__['_headers']['location'])

    def test_process_step_data_working(self):
        self.request.POST = {'next-submit': True}
        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_WORKING)

        ret = SpatialCondorJobMWV().process_step_data(self.request, self.session, self.step, self.model_db,
                                                      self.current_url, self.prev_url, self.next_url)

        msg_call_args = self.mock_message.warning.call_args_list
        self.assertEqual('Please wait for the job to finish running before proceeding.', msg_call_args[0][0][1])
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    def test_process_step_data_failed(self):
        self.request.POST = {'next-submit': True}
        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_FAILED)

        ret = SpatialCondorJobMWV().process_step_data(self.request, self.session, self.step, self.model_db,
                                                      self.current_url, self.prev_url, self.next_url)

        msg_call_args = self.mock_message.error.call_args_list
        self.assertEqual('The job did not finish successfully. Please press "Rerun" to try again.',
                         msg_call_args[0][0][1])
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    def test_process_step_data_pending(self):
        self.request.POST = {'next-submit': True}
        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_PENDING)

        ret = SpatialCondorJobMWV().process_step_data(self.request, self.session, self.step, self.model_db,
                                                      self.current_url, self.prev_url, self.next_url)

        msg_call_args = self.mock_message.info.call_args_list
        self.assertEqual('Please press "Run" to continue.', msg_call_args[0][0][1])
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    def test_run_job_no_request_post(self):
        ret = SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
    def test_run_job_no_active_role(self, mock_get_step):
        mock_get_step.return_value = self.step
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True
        self.mock_active_role.return_value = False

        ret = SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)

        msg_call_args = self.mock_message.warning.call_args_list
        self.assertEqual('You do not have permission to run this workflow.', msg_call_args[0][0][1])
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    def test_run_job_no_schedule_name(self):
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True

        try:
            SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual('Improperly configured SpatialCondorJobRWS: no "scheduler" option supplied.', str(e))

    def test_run_job_no_jobs(self):
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True
        self.step.options['scheduler'] = 'my_schedule'

        try:
            SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual('Improperly configured SpatialCondorJobRWS: no "jobs" option supplied.', str(e))
