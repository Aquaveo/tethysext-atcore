"""
********************************************************************************
* Name: helpers_tests.py
* Author: mlebaron
* Created On: September 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
import unittest
from sqlalchemy.exc import OperationalError, PendingRollbackError
from tethysext.atcore.services.resource_workflows import helpers
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from argparse import Namespace


class HelpersTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_set_step_status(self):
        session = mock.MagicMock()
        step = ResourceWorkflowStep(name='name1', help='help1', order=1)
        step.attributes = {'condor_job_statuses': [step.STATUS_PENDING]}

        helpers.set_step_status(session, step, step.STATUS_COMPLETE)

        self.assertEqual([step.STATUS_PENDING, step.STATUS_COMPLETE], step.get_attribute('condor_job_statuses'))

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_recovers_from_operational_error(self, mock_sessionmaker):
        # First session raises on refresh (simulating a dead connection).
        bad_session = mock.MagicMock()
        bad_session.refresh.side_effect = OperationalError('SELECT 1', {}, Exception('SSL closed'))

        # Fresh session built via sessionmaker() succeeds.
        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session

        step = ResourceWorkflowStep(name='n', help='h', order=1)
        step.attributes = {'condor_job_statuses': [step.STATUS_PENDING]}
        fresh_session.query.return_value.get.return_value = step

        helpers.set_step_status(bad_session, step, step.STATUS_COMPLETE)

        bad_session.invalidate.assert_called_once()
        mock_sessionmaker.assert_called_once_with(bind=bad_session.get_bind.return_value)
        fresh_session.commit.assert_called_once()
        fresh_session.close.assert_called_once()
        self.assertEqual([step.STATUS_PENDING, step.STATUS_COMPLETE], step.get_attribute('condor_job_statuses'))

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_recovers_from_pending_rollback(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bad_session.refresh.side_effect = PendingRollbackError('rollback required')

        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session

        step = ResourceWorkflowStep(name='n', help='h', order=1)
        step.attributes = {'condor_job_statuses': [step.STATUS_PENDING]}
        fresh_session.query.return_value.get.return_value = step

        helpers.set_step_status(bad_session, step, step.STATUS_FAILED)

        bad_session.invalidate.assert_called_once()
        fresh_session.commit.assert_called_once()
        self.assertEqual([step.STATUS_PENDING, step.STATUS_FAILED], step.get_attribute('condor_job_statuses'))

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_propagates_if_retry_also_fails(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bad_session.refresh.side_effect = OperationalError('q', {}, Exception('boom'))

        fresh_session = mock.MagicMock()
        fresh_session.refresh.side_effect = OperationalError('q', {}, Exception('still dead'))
        mock_sessionmaker.return_value.return_value = fresh_session

        step = ResourceWorkflowStep(name='n', help='h', order=1)
        step.attributes = {'condor_job_statuses': []}
        fresh_session.query.return_value.get.return_value = step

        with self.assertRaises(OperationalError):
            helpers.set_step_status(bad_session, step, step.STATUS_COMPLETE)

        fresh_session.close.assert_called_once()

    def test_set_step_status_propagates_non_recoverable_error(self):
        session = mock.MagicMock()
        session.refresh.side_effect = ValueError('not a connection error')

        step = ResourceWorkflowStep(name='n', help='h', order=1)
        step.attributes = {'condor_job_statuses': []}

        with self.assertRaises(ValueError):
            helpers.set_step_status(session, step, step.STATUS_COMPLETE)

        session.invalidate.assert_not_called()

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
