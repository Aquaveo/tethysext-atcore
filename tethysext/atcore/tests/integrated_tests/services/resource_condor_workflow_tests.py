"""
********************************************************************************
* Name: project_upload
* Author: nswain
* Created On: July 31, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
import unittest

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.services.resource_condor_workflow import ResourceCondorWorkflow


class ResourceCondorWorkflowTests(unittest.TestCase):

    def setUp(self):
        mock_resource = mock.MagicMock()
        mock_resource.id = '2323'
        mock_resource.__module__ = 'path_to_module'
        mock_resource.__class__.__name__ = 'class_name'
        self.app = mock.MagicMock(package='foo')
        self.user = mock.MagicMock()
        self.workflow_name = 'workflow_name'
        self.workspace_path = '/tmp'
        self.input_archive_path = '/tmp/abc.zip'
        self.srid = 1001
        self.resource_db_url = 'postgresql://admin:pass@localhost:5432/gssha_res.db'
        self.resource = mock_resource
        self.scenario_id = 1
        self.scheduler = mock.MagicMock()
        self.job_manager = mock.MagicMock()
        self.gs_engine = mock.MagicMock()
        self.puw = ResourceCondorWorkflow(
            app=self.app,
            user=self.user, workflow_name=self.workflow_name,
            workspace_path=self.workspace_path,
            resource_db_url=self.resource_db_url,
            resource=self.resource,
            scheduler=self.scheduler,
            job_manager=self.job_manager,
            status_keys=[Resource.STATUS_OK],
            another_kwarg='something',
        )

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.services.resource_condor_workflow.create_engine')
    @mock.patch('tethysext.atcore.services.resource_condor_workflow.sessionmaker')
    def test_run_job(self, mock_sessionmaker, _):
        mock_session = mock_sessionmaker()()
        mock_resource = mock_session.query().get()
        self.puw.prepare = mock.MagicMock()
        self.puw.workflow = mock.MagicMock()
        self.puw.run_job()

        mock_resource.set_status.assert_called_with(Resource.ROOT_STATUS_KEY,
                                                    Resource.STATUS_PENDING)
        mock_session.commit.assert_called()
        mock_session.close.assert_called()
        self.puw.prepare.assert_called()
        self.puw.workflow.execute.assert_called()

    def test_get_jobs(self):
        got_jobs = self.puw.get_jobs()
        self.assertEqual(got_jobs, [])

    @mock.patch('tethys_compute.models.condor.condor_workflow_job_node.CondorWorkflowJobNode')
    def test_get_prepare(self, mock_job):
        mock_job1 = mock.MagicMock()
        mock_job1.children_nodes.count.return_value = 0
        mock_job2 = mock.MagicMock()
        mock_job2.children_nodes.count.return_value = 1
        mock_job3 = mock.MagicMock()
        mock_job3.children_nodes.count.return_value = 0

        self.puw.get_jobs = mock.MagicMock()
        self.puw.get_jobs.return_value = [(mock_job1, 'run_job1: SUCCESS'),
                                          (mock_job2, 'run_job2: SUCCESS'),
                                          (mock_job3, 'run_job3: SUCCESS')]
        self.puw.job_manager = mock.MagicMock()

        self.puw.prepare()

        self.puw.job_manager.create_job.assert_called_with(
            name=self.puw.safe_job_name,
            user=self.user,
            job_type='CONDORWORKFLOW',
            max_jobs={'geoserver': 1},
            workspace=self.workspace_path,
            scheduler=self.scheduler
        )
        mock_job().save.assert_called()
        self.assertEqual(mock_job().add_parent.call_count, 2)
