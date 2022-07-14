"""
********************************************************************************
* Name: spatial_condor_job_mwv_tests.py
* Author: mlebaron
* Created On: August 16, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
import shutil
from unittest import mock
from django.http import HttpRequest, HttpResponseRedirect
from tethys_sdk.base import TethysAppBase
from tethys_apps.base.workspace import TethysWorkspace
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv import SpatialCondorJobMWV
from tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws import SpatialDatasetRWS
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialCondorJobMwvTests(WorkflowViewTestCase):

    def setUp(self):
        super().setUp()

        tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.working_dir_path = os.path.join(tests_dir, 'files', 'working_dir')

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
        self.model_db = mock.MagicMock(spec=ModelDatabase)
        self.current_url = './current'
        self.next_url = './next'
        self.prev_url = './prev'

        self.resource.id = 12345
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

        if os.path.exists(self.working_dir_path):
            shutil.rmtree(self.working_dir_path)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=False)
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_process_step_options(self, mock_get_managers, _):
        map_view = MapView()
        mock_get_managers.return_value = None, map_view
        instance = SpatialCondorJobMWV()
        instance.map_type = 'tethys_map_view'
        instance.process_step_options(self.request, self.session, self.context, self.resource, self.step, None, None)

        self.assertIn('map_view', self.context)
        self.assertIn('layer_groups', self.context)
        self.assertIn('can_run_workflows', self.context)
        self.assertTrue(self.context['can_run_workflows'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=True)
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_process_step_options__read_only(self, mock_get_managers, _):
        map_view = MapView()
        mock_get_managers.return_value = None, map_view
        instance = SpatialCondorJobMWV()
        instance.map_type = 'tethys_map_view'
        instance.process_step_options(self.request, self.session, self.context, self.resource, self.step, None, None)

        self.assertIn('map_view', self.context)
        self.assertIn('layer_groups', self.context)
        self.assertIn('can_run_workflows', self.context)
        self.assertFalse(self.context['can_run_workflows'])

    def test_on_get_step_pending(self):
        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_PENDING)

        ret = SpatialCondorJobMWV().on_get_step(self.request, self.session, self.resource, self.workflow, self.step,
                                                None, None)

        self.assertEqual(None, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv.'
                'SpatialCondorJobMWV.render_condor_jobs_table')
    def test_on_get_step_not_pending(self, mock_rcjt):
        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_COMPLETE)

        SpatialCondorJobMWV().on_get_step(self.request, self.session, self.resource, self.workflow, self.step,
                                          None, None)

        mock_rcjt.assert_called_with(self.request, self.resource, self.workflow, self.step, None, None)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'workflow_locked_for_request_user', return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv.render')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app')
    def test_render_condor_jobs_table(self, mock_get_app, mock_get_active_app, mock_render, _, __):
        app = mock.MagicMock()
        job_manager = mock.MagicMock()
        job_manager.get_job.return_value = mock.MagicMock()
        app.get_job_manager.return_value = job_manager
        mock_get_app.return_value = app

        active_app = mock.MagicMock()
        active_app.package = 'app_namespace'
        mock_get_active_app.return_value = active_app

        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_COMPLETE)

        SpatialCondorJobMWV().render_condor_jobs_table(self.request, self.resource, self.workflow, self.step,
                                                       None, None)

        arg_call_list = mock_render.call_args_list[0][0][2]
        self.assertEqual(self.resource, arg_call_list['resource'])
        self.assertEqual(self.workflow, arg_call_list['workflow'])
        self.assertIn('steps', arg_call_list)
        self.assertIn('current_step', arg_call_list)
        self.assertIn('next_step', arg_call_list)
        self.assertIn('previous_step', arg_call_list)
        self.assertEqual('app_namespace:generic_workflow_workflow_step', arg_call_list['step_url_name'])
        self.assertIn('next_title', arg_call_list)
        self.assertIn('finish_title', arg_call_list)
        self.assertIn('previous_title', arg_call_list)
        self.assertIn('back_url', arg_call_list)
        self.assertIn('nav_title', arg_call_list)
        self.assertIn('nav_subtitle', arg_call_list)
        self.assertIn('jobs_table', arg_call_list)
        self.assertEqual(1, len(arg_call_list['jobs_table']['jobs']))
        self.assertTrue(arg_call_list['can_run_workflows'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.'
                'workflow_locked_for_request_user', return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=True)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv.render')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app')
    def test_render_condor_jobs_table__read_only(self, mock_get_app, mock_get_active_app, mock_render, _, __):
        app = mock.MagicMock()
        job_manager = mock.MagicMock()
        job_manager.get_job.return_value = mock.MagicMock()
        app.get_job_manager.return_value = job_manager
        mock_get_app.return_value = app

        active_app = mock.MagicMock()
        active_app.package = 'app_namespace'
        mock_get_active_app.return_value = active_app

        self.step.set_status(SpatialDatasetRWS.ROOT_STATUS_KEY, SpatialDatasetRWS.STATUS_COMPLETE)

        SpatialCondorJobMWV().render_condor_jobs_table(self.request, self.resource, self.workflow, self.step,
                                                       None, None)

        arg_call_list = mock_render.call_args_list[0][0][2]
        self.assertEqual(self.resource, arg_call_list['resource'])
        self.assertEqual(self.workflow, arg_call_list['workflow'])
        self.assertIn('steps', arg_call_list)
        self.assertIn('current_step', arg_call_list)
        self.assertIn('next_step', arg_call_list)
        self.assertIn('previous_step', arg_call_list)
        self.assertEqual('app_namespace:generic_workflow_workflow_step', arg_call_list['step_url_name'])
        self.assertIn('next_title', arg_call_list)
        self.assertIn('finish_title', arg_call_list)
        self.assertIn('previous_title', arg_call_list)
        self.assertIn('back_url', arg_call_list)
        self.assertIn('nav_title', arg_call_list)
        self.assertIn('nav_subtitle', arg_call_list)
        self.assertIn('jobs_table', arg_call_list)
        self.assertEqual(1, len(arg_call_list['jobs_table']['jobs']))
        self.assertFalse(arg_call_list['can_run_workflows'])

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

    def test_run_job__submit_not_in_POST_params(self):
        ret = SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=True)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
    def test_run_job__read_only(self, mock_get_step, _):
        mock_get_step.return_value = self.step
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True
        self.mock_active_role.return_value = False

        ret = SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)

        msg_call_args = self.mock_message.warning.call_args_list
        self.assertEqual('You do not have permission to run this workflow.', msg_call_args[0][0][1])
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=False)
    def test_run_job_no_schedule_name(self, _):
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True

        try:
            SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual('Improperly configured SpatialCondorJobRWS: no "scheduler" option supplied.', str(e))

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=False)
    def test_run_job_no_jobs(self, _):
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True
        self.step.options['scheduler'] = 'my_schedule'

        try:
            SpatialCondorJobMWV().run_job(self.request, self.session, self.resource, self.workflow.id, self.step.id)
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertEqual('Improperly configured SpatialCondorJobRWS: no "jobs" option supplied.', str(e))

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only',
                return_value=False)
    @mock.patch('tethysext.atcore.services.workflow_manager.condor_workflow_manager.ResourceWorkflowCondorJobManager.run_job')  # noqa: E501
    @mock.patch('tethysext.atcore.services.workflow_manager.condor_workflow_manager.ResourceWorkflowCondorJobManager.prepare')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_condor_job_mwv.SpatialCondorJobMWV.get_working_directory')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_run_job(self, mock_get_managers, mock_get_working_dir, mock_prepare, mock_run_job, _):
        map_manager = mock.MagicMock(
            spec=MapManagerBase,
            spatial_manager=mock.MagicMock(
                gs_engine=mock.MagicMock(
                    username='Faxy',
                    password='Bear',
                    endpoint='http://localhost:8181/geoserver/rest',
                    public_endpoint='http://localhost:8181/geoserver/rest'
                )
            )
        )

        mock_get_managers.return_value = mock.MagicMock(spec=ModelDatabase), map_manager
        mock_get_working_dir.return_value = os.path.join(self.working_dir_path, 'working_dir')
        mock_prepare.return_value = self.workflow.id
        mock_run_job.return_value = str(self.workflow.id)

        session = mock.MagicMock()
        self.step.workflow = mock.MagicMock()
        self.step.workflow.resource = self.resource
        user = UserFactory()
        self.request.user = user
        self.request.POST['run-submit'] = True
        self.request.POST['rerun-submit'] = True
        self.step.options['scheduler'] = 'my_schedule'
        job = {
            'name': 'base_scenario',
            'condorpy_template_name': 'vanilla_transfer_files',
            'remote_input_files': [None],
            'attributes': {
                'executable': 'run_base_scenario.py',
                'transfer_output_files': ['gssha_files', 'base_ohl_series.json']
            }
        }
        self.step.options['jobs'] = [job]

        ret = SpatialCondorJobMWV().run_job(self.request, session, self.resource, self.workflow.id, self.step.id)

        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(self.request.path, ret.url)

    def test_get_working_directory(self):
        user = UserFactory()
        self.request.user = user
        app = mock.MagicMock(spec=TethysAppBase)
        app.get_user_workspace.return_value = TethysWorkspace('user_workspace')

        path = SpatialCondorJobMWV().get_working_directory(self.request, app)

        self.assertEqual('user_workspace', path)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_previous_steps')
    def test_serialize_parameters(self, mock_get_prev_steps):
        mock_get_prev_steps.return_value = [self.step]

        ret = SpatialCondorJobMWV().serialize_parameters(self.step)

        self.assertEqual('{"name1": {"type": "spatial_dataset_workflow_step", "name": "name1", "help": "help1", '
                         '"parameters": {"datasets": {}}}}', ret)
