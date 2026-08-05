"""
********************************************************************************
* Name: helpers_tests.py
* Author: mlebaron
* Created On: September 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
import os
import tempfile
import unittest
from sqlalchemy.exc import OperationalError, PendingRollbackError
from tethysext.atcore.services.resource_workflows import helpers
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from argparse import Namespace

NODE = 'original_scenario_2yr'


def bind_locking_query(session, step):
    """Point the row-locking query chain of a mocked session at the given step."""
    query = session.query.return_value
    query.populate_existing.return_value.with_for_update.return_value \
        .filter_by.return_value.one.return_value = step
    return query.populate_existing.return_value.with_for_update.return_value \
        .filter_by.return_value


class HelpersTests(unittest.TestCase):

    def setUp(self):
        self.step = ResourceWorkflowStep(name='name1', help='help1', order=1)

    def tearDown(self):
        pass

    def test_set_step_status(self):
        session = mock.MagicMock()
        self.step.attributes = {'condor_job_statuses': {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        self.assertEqual(
            {NODE: self.step.STATUS_COMPLETE},
            self.step.get_attribute('condor_job_statuses'),
        )
        session.commit.assert_called_once()

    def test_set_step_status_locks_the_row(self):
        session = mock.MagicMock()
        self.step.attributes = {'condor_job_statuses': {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        session.query.return_value.populate_existing.return_value \
            .with_for_update.assert_called_once()

    def test_set_step_status_keeps_other_nodes(self):
        session = mock.MagicMock()
        self.step.attributes = {'condor_job_statuses': {'other_node': self.step.STATUS_COMPLETE}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        self.assertEqual(
            {'other_node': self.step.STATUS_COMPLETE, NODE: self.step.STATUS_FAILED},
            self.step.get_attribute('condor_job_statuses'),
        )

    def test_set_step_status_retry_overwrites_previous_status(self):
        """A node that fails and then succeeds must not leave the failure behind."""
        session = mock.MagicMock()
        self.step.attributes = {'condor_job_statuses': {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)
        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        self.assertEqual(
            {NODE: self.step.STATUS_COMPLETE},
            self.step.get_attribute('condor_job_statuses'),
        )
        self.assertNotIn(self.step.STATUS_FAILED, helpers.get_step_statuses(self.step))

    def test_set_step_status_migrates_legacy_list(self):
        session = mock.MagicMock()
        self.step.attributes = {'condor_job_statuses': [self.step.STATUS_COMPLETE]}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        self.assertEqual(
            {'_legacy_0': self.step.STATUS_COMPLETE, NODE: self.step.STATUS_FAILED},
            self.step.get_attribute('condor_job_statuses'),
        )

    def test_set_step_status_resolves_node_name_when_not_given(self):
        session = mock.MagicMock()
        self.step.attributes = {'condor_job_statuses': {}}
        bind_locking_query(session, self.step)

        with mock.patch.object(helpers, 'dag_node_name', return_value='resolved_node'):
            helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE)

        self.assertEqual(
            {'resolved_node': self.step.STATUS_COMPLETE},
            self.step.get_attribute('condor_job_statuses'),
        )

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_recovers_from_operational_error(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bind_locking_query(bad_session, self.step).one.side_effect = OperationalError(
            'SELECT 1', {}, Exception('SSL closed')
        )

        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session

        self.step.attributes = {'condor_job_statuses': {}}
        fresh_session.query.return_value.get.return_value = self.step
        bind_locking_query(fresh_session, self.step)

        helpers.set_step_status(bad_session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        bad_session.invalidate.assert_called_once()
        mock_sessionmaker.assert_called_once_with(bind=bad_session.get_bind.return_value)
        fresh_session.commit.assert_called_once()
        fresh_session.close.assert_called_once()
        self.assertEqual(
            {NODE: self.step.STATUS_COMPLETE},
            self.step.get_attribute('condor_job_statuses'),
        )

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_recovers_from_pending_rollback(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bind_locking_query(bad_session, self.step).one.side_effect = PendingRollbackError(
            'rollback required'
        )

        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session

        self.step.attributes = {'condor_job_statuses': {}}
        fresh_session.query.return_value.get.return_value = self.step
        bind_locking_query(fresh_session, self.step)

        helpers.set_step_status(bad_session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        bad_session.invalidate.assert_called_once()
        fresh_session.commit.assert_called_once()
        self.assertEqual(
            {NODE: self.step.STATUS_FAILED},
            self.step.get_attribute('condor_job_statuses'),
        )

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_propagates_if_retry_also_fails(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bind_locking_query(bad_session, self.step).one.side_effect = OperationalError(
            'q', {}, Exception('boom')
        )

        fresh_session = mock.MagicMock()
        bind_locking_query(fresh_session, self.step).one.side_effect = OperationalError(
            'q', {}, Exception('still dead')
        )
        mock_sessionmaker.return_value.return_value = fresh_session

        self.step.attributes = {'condor_job_statuses': {}}
        fresh_session.query.return_value.get.return_value = self.step

        with self.assertRaises(OperationalError):
            helpers.set_step_status(bad_session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        fresh_session.close.assert_called_once()

    def test_set_step_status_propagates_non_recoverable_error(self):
        session = mock.MagicMock()
        bind_locking_query(session, self.step).one.side_effect = ValueError(
            'not a connection error'
        )

        self.step.attributes = {'condor_job_statuses': {}}

        with self.assertRaises(ValueError):
            helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        session.invalidate.assert_not_called()

    def test_dag_node_name_from_job_ad(self):
        with tempfile.NamedTemporaryFile('w', suffix='.ad', delete=False) as job_ad:
            job_ad.write('DAGManJobId = 423\n')
            job_ad.write('DAGNodeName = "{}"\n'.format(NODE))
            path = job_ad.name

        try:
            with mock.patch.dict(os.environ, {'_CONDOR_JOB_AD': path}):
                self.assertEqual(NODE, helpers.dag_node_name())
        finally:
            os.unlink(path)

    def test_dag_node_name_without_job_ad_is_unique(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            name = helpers.dag_node_name()

        self.assertTrue(name.startswith('unknown_'))
        self.assertIn(str(os.getpid()), name)

    def test_dag_node_name_unreadable_job_ad(self):
        with mock.patch.dict(os.environ, {'_CONDOR_JOB_AD': '/nonexistent/job.ad'}):
            name = helpers.dag_node_name()

        self.assertTrue(name.startswith('unknown_'))

    def test_dag_node_name_job_ad_without_node_name(self):
        with tempfile.NamedTemporaryFile('w', suffix='.ad', delete=False) as job_ad:
            job_ad.write('ClusterId = 12\n')
            path = job_ad.name

        try:
            with mock.patch.dict(os.environ, {'_CONDOR_JOB_AD': path}):
                self.assertTrue(helpers.dag_node_name().startswith('unknown_'))
        finally:
            os.unlink(path)

    def test_get_step_statuses_from_dict(self):
        self.step.attributes = {'condor_job_statuses': {'a': 'Complete', 'b': 'Failed'}}

        self.assertCountEqual(['Complete', 'Failed'], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_from_legacy_list(self):
        self.step.attributes = {'condor_job_statuses': ['Complete', 'Failed']}

        self.assertCountEqual(['Complete', 'Failed'], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_when_unset(self):
        self.step.attributes = {}

        self.assertEqual([], helpers.get_step_statuses(self.step))

    @mock.patch('argparse._sys')
    def test_parse_workflow_step_args(self, mock_sys):
        mock_sys.argv = ['prog']
        ret, _ = helpers.parse_workflow_step_args()

        self.assertIsInstance(ret, Namespace)

    @mock.patch('argparse._sys')
    def test_parse_workflow_step_args_with_extra(self, mock_sys):
        # No extra arguments
        mock_sys.argv = ['prog']
        ret, extra_args = helpers.parse_workflow_step_args()
        self.assertIsInstance(ret, Namespace)
        self.assertListEqual(extra_args, [])

        # Extra (optional) arguments
        mock_sys.argv = ['prog', '--extra_arg', '--extra_arg_2']  # Extra arguments
        ret, extra_args = helpers.parse_workflow_step_args()
        self.assertIsInstance(ret, Namespace)
        self.assertListEqual(extra_args, ['--extra_arg', '--extra_arg_2'])

        # Extra arguments after all of the required (and optional) job arguments
        mock_sys.argv = ['prog', 'resource_db_url', 'model_db_url', 'resource_id', 'resource_workflow_id',
                         'resource_workflow_step_id', 'gs_private_url', 'gs_public_url', 'resource_class',
                         'workflow_class', 'workflow_params_file', '-s', 'scenario_id', '-a', 'app_workspace',
                         'extra_argument_1', 'extra_argument_2', 'extra_argument_3']

        ret, extra_args = helpers.parse_workflow_step_args()
        self.assertIsInstance(ret, Namespace)
        self.assertListEqual(extra_args, ['extra_argument_1', 'extra_argument_2', 'extra_argument_3'])
