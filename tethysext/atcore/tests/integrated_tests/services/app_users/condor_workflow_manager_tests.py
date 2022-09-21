"""
********************************************************************************update_status.py
* Name: condor_workflow_manager_tests.py
* Author: mlebaron
* Created On: September 4, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
import pathlib as pl
import tethys_apps.base.app_base as tethys_app_base
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.services.workflow_manager.condor_workflow_manager import ResourceWorkflowCondorJobManager as Manager  # noqa: E501
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from tethysext.atcore.models.app_users import Resource
from tethys_compute.models.condor.condor_workflow import CondorWorkflow
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethys_compute.models.condor.condor_scheduler import CondorScheduler
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MockGeoServerEngine(object):

    def __init__(self, endpoint, public_endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.public_endpoint = public_endpoint


class CondorWorkflowManagerTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        tests_dir = pl.Path(__file__).parents[3]
        self.key_path = tests_dir / 'files' / 'keys' / 'testkey'

        self.model_db = mock.MagicMock()
        self.model_db.db_url = 'some_url'

        self.user = UserFactory()
        self.user.username = 'John Doe'
        self.user.save()

        self.scheduler_name = 'some_scheduler'
        self.scheduler = CondorScheduler.objects.create(
            name=self.scheduler_name,
            host='localhost',
            username=self.user.username,
            password='pass',
            private_key_path=self.key_path,
            private_key_pass='test_pass'
        )
        self.scheduler.save()

        self.step = ResourceWorkflowStep(
            name='step_name',
            help='Helpfulness'
        )

        self.workflow = ResourceWorkflow(name='workflow_name')
        self.workflow.steps.append(self.step)
        self.workflow.resource = Resource(
            name='resource_name'
        )
        self.session.add(self.workflow)
        self.session.commit()

        self.session.get_bind().url = 'some_db_url'

        self.working_directory = 'path/to/dir'

        self.app = tethys_app_base.TethysAppBase()

        base_job = {
            'name': 'base_scenario',
            'condorpy_template_name': 'vanilla_transfer_files',
            'remote_input_files': ["/path/to/base/files"],
            'attributes': {
                'executable': 'run_base_scenario.py',
                'transfer_output_files': [
                    'gssha_files',
                    'base_ohl_series.json'
                ],
            },
        }

        dt_job = {
            'name': 'detention_basin_scenario',
            'condorpy_template_name': 'vanilla_transfer_files',
            'remote_input_files': ["/path/to/dt/files"],
            'attributes': {
                'executable': 'run_detention_basin_scenario.py',
                'transfer_output_files': [
                    'gssha_files',
                    'detention_basin_ohl_series.json'
                ],
            },
        }

        post_process_job = {
            'name': 'post_processing',
            'condorpy_template_name': 'vanilla_transfer_files',
            'remote_input_files': ["/path/to/pp/files"],
            'attributes': {
                'executable': 'post_process.py',
                'transfer_output_files': [],
                'transfer_input_files': [
                    '../base_scenario/base_ohl_series.json',
                    '../detention_basin_scenario/detention_basin_ohl_series.json',
                ],
            },
            'parents': [base_job['name'], dt_job['name']]
        }

        self.jobs = [
            base_job,
            dt_job,
            post_process_job
        ]

    def tearDown(self):
        super().tearDown()

    def test_init(self):
        manager = Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                          self.scheduler_name, jobs=self.jobs)

        self.assertEqual(self.session.get_bind().url, manager.resource_db_url)
        self.assertEqual(self.model_db.db_url, manager.model_db_url)
        self.assertEqual('', manager.gs_private_url)
        self.assertEqual('', manager.gs_public_url)
        self.assertEqual(str(self.step.workflow.resource.id), manager.resource_id)
        self.assertEqual(self.workflow.resource.name, manager.resource_name)
        self.assertEqual(str(self.workflow.id), manager.resource_workflow_id)
        self.assertEqual(self.workflow.name, manager.resource_workflow_name)
        self.assertEqual('Generic Workflow', manager.resource_workflow_type)
        self.assertEqual(str(self.step.id), manager.resource_workflow_step_id)
        self.assertEqual(self.step.name, manager.resource_workflow_step_name)
        self.assertEqual(self.jobs, manager.jobs)
        self.assertTrue(manager.jobs_are_dicts)
        self.assertEqual(self.user, manager.user)
        self.assertEqual(self.working_directory, manager.working_directory)
        self.assertEqual(self.app, manager.app)
        self.assertEqual(self.scheduler_name, manager.scheduler_name)
        self.assertEqual([], manager.input_files)
        self.assertEqual(self.step.name, manager.safe_job_name)
        expected_job_args = [
            self.session.get_bind().url,
            self.model_db.db_url,
            str(self.workflow.resource.id),
            str(self.workflow.id),
            str(self.step.id),
            '',
            '',
            str(manager._get_class_path(self.workflow.resource)),
            str(manager._get_class_path(self.workflow)),
        ]
        self.assertEqual(expected_job_args, manager.job_args)
        self.assertEqual(None, manager.workflow)
        self.assertFalse(manager.prepared)
        self.assertFalse(manager.workspace_initialized)
        self.assertEqual(None, manager._workspace_path)

    def test_init_with_optional_params(self):
        input_files = ['file1.txt', 'file2.xyz']
        gs_engine = MockGeoServerEngine(
            endpoint="http://localhost:8181/geoserver/rest/",
            username="admin",
            password="geoserver",
            public_endpoint="http://aquaveo.com/geoserver/rest/",
        )
        expected_private_url = 'http://admin:geoserver@localhost:8181/geoserver/rest/'
        expected_public_url = 'http://admin:geoserver@aquaveo.com/geoserver/rest/'

        manager = Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                          self.scheduler_name, jobs=self.jobs, input_files=input_files, gs_engine=gs_engine)

        self.assertEqual(self.session.get_bind().url, manager.resource_db_url)
        self.assertEqual(self.model_db.db_url, manager.model_db_url)
        self.assertEqual(expected_private_url, manager.gs_private_url)
        self.assertEqual(expected_public_url, manager.gs_public_url)
        self.assertEqual(str(self.step.workflow.resource.id), manager.resource_id)
        self.assertEqual(self.workflow.resource.name, manager.resource_name)
        self.assertEqual(str(self.workflow.id), manager.resource_workflow_id)
        self.assertEqual(self.workflow.name, manager.resource_workflow_name)
        self.assertEqual('Generic Workflow', manager.resource_workflow_type)
        self.assertEqual(str(self.step.id), manager.resource_workflow_step_id)
        self.assertEqual(self.step.name, manager.resource_workflow_step_name)
        self.assertEqual(self.jobs, manager.jobs)
        self.assertTrue(manager.jobs_are_dicts)
        self.assertEqual(self.user, manager.user)
        self.assertEqual(self.working_directory, manager.working_directory)
        self.assertEqual(self.app, manager.app)
        self.assertEqual(self.scheduler_name, manager.scheduler_name)
        self.assertEqual(input_files, manager.input_files)
        self.assertEqual(self.step.name, manager.safe_job_name)
        expected_job_args = [
            self.session.get_bind().url,
            self.model_db.db_url,
            str(self.workflow.resource.id),
            str(self.workflow.id),
            str(self.step.id),
            expected_private_url,
            expected_public_url,
            str(manager._get_class_path(self.workflow.resource)),
            str(manager._get_class_path(self.workflow)),
        ]
        self.assertEqual(expected_job_args, manager.job_args)
        self.assertEqual(None, manager.workflow)
        self.assertFalse(manager.prepared)
        self.assertFalse(manager.workspace_initialized)
        self.assertEqual(None, manager._workspace_path)

    def test_init_no_jobs(self):
        try:
            Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                    self.scheduler_name, jobs=None)
            self.assertTrue(False)  # This line should not be reached
        except ValueError as e:
            self.assertEqual('Argument "jobs" is not defined or empty. Must provide at least one CondorWorkflowJobNode '
                             'or equivalent dictionary.', str(e))

    def test_workspace_no_path(self):
        manager = Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                          self.scheduler_name, jobs=self.jobs)
        expected_path = f'{self.working_directory}/{str(self.workflow.id)}/{str(self.step.id)}/{self.step.name}'

        path = manager.workspace

        self.assertEqual(expected_path, path)
        self.assertTrue(manager.workspace_initialized)

    def test_prepare(self):
        self.app.get_scheduler = mock.MagicMock(return_value=self.scheduler)
        manager = Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                          self.scheduler_name, jobs=self.jobs, input_files=[self.key_path])

        id = manager.prepare()

        # Job 1
        self.assertEqual(self.jobs[0]['name'], manager.jobs[0].name)
        self.assertEqual(1, manager.jobs[0].workflow.id)
        self.assertEqual(1, manager.jobs[0].workflow_id)
        self.assertEqual(self.jobs[0]['name'], manager.jobs[0]._attributes['job_name'])
        self.assertEqual('vanilla', manager.jobs[0]._attributes['universe'])
        self.assertEqual('run_base_scenario.py', manager.jobs[0]._attributes['executable'])
        expected_args = f'{self.session.get_bind().url} {self.model_db.db_url} {self.workflow.resource.id} ' \
            f'{self.workflow.id} {self.step.id}   {manager._get_class_path(self.workflow.resource)} ' \
            f'{manager._get_class_path(self.workflow)} testkey'
        self.assertEqual(expected_args, manager.jobs[0]._attributes['arguments'])
        self.assertEqual(', ../testkey', manager.jobs[0]._attributes['transfer_input_files'])
        self.assertEqual('gssha_files, base_ohl_series.json', manager.jobs[0]._attributes['transfer_output_files'])

        # Job 2
        self.assertEqual(self.jobs[1]['name'], manager.jobs[1].name)
        self.assertEqual(1, manager.jobs[1].workflow.id)
        self.assertEqual(1, manager.jobs[1].workflow_id)
        self.assertEqual(self.jobs[1]['name'], manager.jobs[1]._attributes['job_name'])
        self.assertEqual('vanilla', manager.jobs[1]._attributes['universe'])
        self.assertEqual('run_detention_basin_scenario.py', manager.jobs[1]._attributes['executable'])
        self.assertEqual(expected_args, manager.jobs[1]._attributes['arguments'])
        self.assertEqual(', ../testkey', manager.jobs[1]._attributes['transfer_input_files'])
        self.assertEqual('gssha_files, detention_basin_ohl_series.json',
                         manager.jobs[1]._attributes['transfer_output_files'])

        # Job 3
        self.assertEqual(self.jobs[2]['name'], manager.jobs[2].name)
        self.assertEqual(1, manager.jobs[2].workflow.id)
        self.assertEqual(1, manager.jobs[2].workflow_id)
        self.assertEqual(self.jobs[2]['name'], manager.jobs[2]._attributes['job_name'])
        self.assertEqual('vanilla', manager.jobs[2]._attributes['universe'])
        self.assertEqual('post_process.py', manager.jobs[2]._attributes['executable'])
        self.assertEqual(expected_args, manager.jobs[2]._attributes['arguments'])
        self.assertEqual('../base_scenario/base_ohl_series.json,  '
                         '../detention_basin_scenario/detention_basin_ohl_series.json, ../testkey',
                         manager.jobs[2]._attributes['transfer_input_files'])
        self.assertEqual('', manager.jobs[2]._attributes['transfer_output_files'])

        # Job 4
        self.assertEqual('finalize', manager.jobs[3].name)
        self.assertEqual(1, manager.jobs[3].workflow.id)
        self.assertEqual(1, manager.jobs[3].workflow_id)
        self.assertEqual('finalize', manager.jobs[3]._attributes['job_name'])
        self.assertEqual('vanilla', manager.jobs[3]._attributes['universe'])
        self.assertEqual('update_status.py', manager.jobs[3]._attributes['executable'])
        self.assertEqual(expected_args, manager.jobs[3]._attributes['arguments'])
        self.assertEqual('../workflow_params.json', manager.jobs[3]._attributes['transfer_input_files'])
        self.assertEqual('', manager.jobs[3]._attributes['transfer_output_files'])

        self.assertEqual(1, id)
        self.assertIsInstance(manager.workflow, CondorWorkflow)
        expected_job_args = [
            self.session.get_bind().url,
            self.model_db.db_url,
            str(self.workflow.resource.id),
            str(self.workflow.id),
            str(self.step.id),
            '',
            '',
            str(manager._get_class_path(self.workflow.resource)),
            str(manager._get_class_path(self.workflow)),
            'testkey'
        ]
        self.assertEqual(expected_job_args, manager.job_args)
        self.assertTrue(manager.prepared)

    @mock.patch('tethys_compute.models.tethys_job.TethysJob.execute')
    def test_run_job_prepared(self, _):
        self.app.get_scheduler = mock.MagicMock(return_value=self.scheduler)
        manager = Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                          self.scheduler_name, jobs=self.jobs)
        manager.prepared = False

        id = manager.run_job()

        self.assertEqual(str(2), id)
