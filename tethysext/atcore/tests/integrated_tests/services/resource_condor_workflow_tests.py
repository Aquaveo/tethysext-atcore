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
        self.user = mock.MagicMock()
        self.workflow_name = 'workflow_name'
        self.workspace_path = '/tmp'
        self.input_archive_path = '/tmp/abc.zip'
        self.srid = 1001
        self.resource_db_url = 'postgresql://admin:pass@localhost:5432/gssha_res.db'
        self.resource_id = '2323'
        self.scenario_id = 1
        self.scheduler = mock.MagicMock(),
        self.job_manager = mock.MagicMock(),
        self.model_db = mock.MagicMock()
        self.gs_engine = mock.MagicMock()
        self.puw = ResourceCondorWorkflow(
            user=self.user, workflow_name=self.workflow_name,
            workspace_path=self.workspace_path,
            resource_db_url=self.resource_db_url,
            resource_id=self.resource_id,
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

    def test_get_prepare(self):
        self.job_manager.create_job = mock.MagicMock()
        got_jobs = self.puw.prepare()
