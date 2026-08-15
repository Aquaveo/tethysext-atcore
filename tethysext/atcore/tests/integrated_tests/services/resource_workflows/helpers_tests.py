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
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, PendingRollbackError
from sqlalchemy.orm import sessionmaker
from tethysext.atcore.services.resource_workflows import helpers
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep, initialize_app_users_db
from tethysext.atcore.tests import TEST_DB_URL
from argparse import Namespace

NODE = 'original_scenario_2yr'
STATUSES = helpers.CONDOR_JOB_STATUSES_BY_NODE_KEY
MIRROR = helpers.CONDOR_JOB_STATUSES_KEY


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
        helpers.dag_node_name.cache_clear()

    def tearDown(self):
        pass

    def test_set_step_status(self):
        session = mock.MagicMock()
        self.step.attributes = {STATUSES: {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        self.assertEqual(
            {NODE: self.step.STATUS_COMPLETE},
            self.step.get_attribute(STATUSES),
        )
        session.commit.assert_called_once()

    def test_set_step_status_locks_the_row(self):
        session = mock.MagicMock()
        self.step.attributes = {STATUSES: {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        session.query.return_value.populate_existing.return_value \
            .with_for_update.assert_called_once()

    def test_set_step_status_keeps_other_nodes(self):
        session = mock.MagicMock()
        self.step.attributes = {STATUSES: {'other_node': self.step.STATUS_COMPLETE}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        self.assertEqual(
            {'other_node': self.step.STATUS_COMPLETE, NODE: self.step.STATUS_FAILED},
            self.step.get_attribute(STATUSES),
        )

    def test_set_step_status_retry_overwrites_previous_status(self):
        """A node that fails and then succeeds must not leave the failure behind."""
        session = mock.MagicMock()
        self.step.attributes = {STATUSES: {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)
        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        self.assertEqual(
            {NODE: self.step.STATUS_COMPLETE},
            self.step.get_attribute(STATUSES),
        )
        self.assertNotIn(self.step.STATUS_FAILED, helpers.get_step_statuses(self.step))

    def test_set_step_status_migrates_legacy_list(self):
        session = mock.MagicMock()
        self.step.attributes = {MIRROR: [self.step.STATUS_COMPLETE]}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        self.assertEqual(
            {'_legacy_0': self.step.STATUS_COMPLETE, NODE: self.step.STATUS_FAILED},
            self.step.get_attribute(STATUSES),
        )

    def test_set_step_status_resolves_node_name_when_not_given(self):
        session = mock.MagicMock()
        self.step.attributes = {STATUSES: {}}
        bind_locking_query(session, self.step)

        with mock.patch.object(helpers, 'dag_node_name', return_value='resolved_node'):
            helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE)

        self.assertEqual(
            {'resolved_node': self.step.STATUS_COMPLETE},
            self.step.get_attribute(STATUSES),
        )

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_recovers_from_operational_error(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bind_locking_query(bad_session, self.step).one.side_effect = OperationalError(
            'SELECT 1', {}, Exception('SSL closed')
        )

        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session

        self.step.attributes = {STATUSES: {}}
        fresh_session.query.return_value.get.return_value = self.step
        bind_locking_query(fresh_session, self.step)

        helpers.set_step_status(bad_session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        bad_session.invalidate.assert_called_once()
        mock_sessionmaker.assert_called_once_with(bind=bad_session.get_bind.return_value)
        fresh_session.commit.assert_called_once()
        fresh_session.close.assert_called_once()
        self.assertEqual(
            {NODE: self.step.STATUS_COMPLETE},
            self.step.get_attribute(STATUSES),
        )

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_recovers_from_pending_rollback(self, mock_sessionmaker):
        bad_session = mock.MagicMock()
        bind_locking_query(bad_session, self.step).one.side_effect = PendingRollbackError(
            'rollback required'
        )

        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session

        self.step.attributes = {STATUSES: {}}
        fresh_session.query.return_value.get.return_value = self.step
        bind_locking_query(fresh_session, self.step)

        helpers.set_step_status(bad_session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        bad_session.invalidate.assert_called_once()
        fresh_session.commit.assert_called_once()
        self.assertEqual(
            {NODE: self.step.STATUS_FAILED},
            self.step.get_attribute(STATUSES),
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

        self.step.attributes = {STATUSES: {}}
        fresh_session.query.return_value.get.return_value = self.step

        with self.assertRaises(OperationalError):
            helpers.set_step_status(bad_session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        fresh_session.close.assert_called_once()

    def test_set_step_status_propagates_non_recoverable_error(self):
        session = mock.MagicMock()
        bind_locking_query(session, self.step).one.side_effect = ValueError(
            'not a connection error'
        )

        self.step.attributes = {STATUSES: {}}

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
        self.step.attributes = {STATUSES: {'a': 'Complete', 'b': 'Failed'}}

        self.assertCountEqual(['Complete', 'Failed'], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_from_legacy_list(self):
        self.step.attributes = {MIRROR: ['Complete', 'Failed']}

        self.assertCountEqual(['Complete', 'Failed'], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_when_unset(self):
        self.step.attributes = {}

        self.assertEqual([], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_prefers_per_node_over_mirror(self):
        """The mirror is written for rolled-back code; the per-node store is authoritative."""
        self.step.attributes = {STATUSES: {'a': 'Complete'}, MIRROR: ['Stale']}

        self.assertEqual(['Complete'], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_from_pre_release_dict_under_old_key(self):
        """A build of this change that shipped before the mirror existed wrote a dict here."""
        self.step.attributes = {MIRROR: {'a': 'Complete', 'b': 'Failed'}}

        self.assertCountEqual(['Complete', 'Failed'], helpers.get_step_statuses(self.step))

    def test_get_step_statuses_ignores_a_scalar(self):
        """list('Failed') would yield characters, which would break the FAILED membership test."""
        self.step.attributes = {MIRROR: 'Failed'}

        self.assertEqual([], helpers.get_step_statuses(self.step))

    def test_set_step_status_writes_the_legacy_mirror(self):
        """Code rolled back to before the per-node store must still find a list here."""
        session = mock.MagicMock()
        self.step.attributes = {STATUSES: {'other_node': self.step.STATUS_COMPLETE}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_FAILED, node_name=NODE)

        mirror = self.step.get_attribute(MIRROR)
        self.assertIsInstance(mirror, list)
        self.assertCountEqual([self.step.STATUS_COMPLETE, self.step.STATUS_FAILED], mirror)

    def test_set_step_status_bounds_the_lock_wait_on_postgres(self):
        session = mock.MagicMock()
        session.get_bind.return_value.dialect.name = 'postgresql'
        self.step.attributes = {STATUSES: {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        statements = [str(call.args[0]) for call in session.execute.call_args_list if call.args]
        self.assertTrue(
            any('lock_timeout' in statement for statement in statements),
            'expected a lock_timeout to be set before taking the row lock, got {}'.format(statements),
        )

    def test_set_step_status_skips_lock_timeout_on_other_backends(self):
        """SET LOCAL lock_timeout is Postgres syntax; do not send it to another backend."""
        session = mock.MagicMock()
        session.get_bind.return_value.dialect.name = 'sqlite'
        self.step.attributes = {STATUSES: {}}
        bind_locking_query(session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        session.execute.assert_not_called()

    def test_dag_node_name_is_stable_within_the_process(self):
        """A job reports more than once; the fallback embeds a timestamp, so it must be cached."""
        with mock.patch.dict(os.environ, {}, clear=True):
            first = helpers.dag_node_name()
            second = helpers.dag_node_name()

        self.assertEqual(first, second)

    def test_set_step_status_retries_a_lock_timeout_without_discarding_the_connection(self):
        """Contention is not a broken connection; invalidate() would throw away a good one."""
        session = mock.MagicMock()
        lock_timeout = OperationalError('SELECT 1', {}, Exception('canceled'))
        lock_timeout.orig.pgcode = helpers.LOCK_NOT_AVAILABLE

        self.step.attributes = {STATUSES: {}}
        locking = bind_locking_query(session, self.step)
        locking.one.side_effect = [lock_timeout, self.step]

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        session.invalidate.assert_not_called()
        session.rollback.assert_called_once()
        self.assertEqual({NODE: self.step.STATUS_COMPLETE}, self.step.get_attribute(STATUSES))

    @mock.patch('tethysext.atcore.services.resource_workflows.helpers.sessionmaker')
    def test_set_step_status_still_invalidates_a_dead_connection(self, mock_sessionmaker):
        """A non-lock-timeout OperationalError is a dead connection and must be evicted."""
        session = mock.MagicMock()
        dead = OperationalError('SELECT 1', {}, Exception('SSL closed'))
        dead.orig.pgcode = '08006'
        bind_locking_query(session, self.step).one.side_effect = dead

        fresh_session = mock.MagicMock()
        mock_sessionmaker.return_value.return_value = fresh_session
        self.step.attributes = {STATUSES: {}}
        fresh_session.query.return_value.get.return_value = self.step
        bind_locking_query(fresh_session, self.step)

        helpers.set_step_status(session, self.step, self.step.STATUS_COMPLETE, node_name=NODE)

        session.invalidate.assert_called_once()
        fresh_session.commit.assert_called_once()

    def test_is_lock_timeout(self):
        lock_timeout = OperationalError('q', {}, Exception('canceled'))
        lock_timeout.orig.pgcode = helpers.LOCK_NOT_AVAILABLE
        other = OperationalError('q', {}, Exception('boom'))
        other.orig.pgcode = '08006'

        self.assertTrue(helpers._is_lock_timeout(lock_timeout))
        self.assertFalse(helpers._is_lock_timeout(other))
        self.assertFalse(helpers._is_lock_timeout(PendingRollbackError('rollback required')))

    def test_initialize_step_statuses_clears_both_shapes(self):
        self.step.attributes = {STATUSES: {'a': 'Failed'}, MIRROR: ['Failed']}

        helpers.initialize_step_statuses(self.step)

        self.assertEqual({}, self.step.get_attribute(STATUSES))
        self.assertEqual([], self.step.get_attribute(MIRROR))


class SetStepStatusConcurrencyTests(unittest.TestCase):
    """
    Exercises the row lock against a real database.

    The mocked tests above can only show that with_for_update() was called. Whether it
    actually serializes two writers is a property of the database, so it needs real
    connections: the shared-connection fixture used elsewhere in this suite runs every
    test inside one transaction, which cannot demonstrate two transactions contending.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(TEST_DB_URL, connect_args={'connect_timeout': 5})
        try:
            cls.engine.connect().close()
        except OperationalError as e:
            raise unittest.SkipTest('test database at {} is unreachable: {}'.format(TEST_DB_URL, e))
        initialize_app_users_db(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        helpers.dag_node_name.cache_clear()
        self.session = self.Session()
        self.workflow = ResourceWorkflow(name='concurrency_test')
        self.step = ResourceWorkflowStep(name='concurrency_step', help='h', order=1)
        self.step.attributes = {STATUSES: {}}
        self.workflow.steps = [self.step]
        self.session.add(self.workflow)
        self.session.commit()
        self.step_id = self.step.id

    def tearDown(self):
        self.session.rollback()
        self.session.delete(self.session.query(ResourceWorkflow).get(self.workflow.id))
        self.session.commit()
        self.session.close()

    def _fresh_step(self, session):
        return session.query(ResourceWorkflowStep).get(self.step_id)

    def test_concurrent_writers_do_not_lose_a_status(self):
        """The bug this guards: a lost FAILED makes a failed workflow report success."""
        session_a = self.Session()
        session_b = self.Session()
        try:
            helpers.set_step_status(session_a, self._fresh_step(session_a), 'Failed', node_name='node_a')
            helpers.set_step_status(session_b, self._fresh_step(session_b), 'Complete', node_name='node_b')
        finally:
            session_a.close()
            session_b.close()

        self.session.expire_all()
        statuses = helpers.get_step_statuses(self._fresh_step(self.session))
        self.assertCountEqual(['Failed', 'Complete'], statuses)

    def test_second_writer_blocks_while_the_row_is_locked(self):
        """Proves the lock is real: a held row lock must stop another writer, not be ignored."""
        holder = self.Session()
        contender = self.Session()
        try:
            # Take and hold the same lock _record_status takes, without committing.
            holder.query(ResourceWorkflowStep).populate_existing().with_for_update() \
                .filter_by(id=self.step_id).one()

            with mock.patch.object(helpers, 'STATUS_LOCK_TIMEOUT_MS', 500):
                # Both the first attempt and set_step_status's one retry must hit the lock.
                with self.assertRaises(OperationalError):
                    helpers.set_step_status(
                        contender, self._fresh_step(contender), 'Complete', node_name='blocked_node',
                    )
        finally:
            holder.rollback()
            holder.close()
            contender.rollback()
            contender.close()

        # Nothing from the blocked writer was persisted.
        self.session.expire_all()
        self.assertEqual([], helpers.get_step_statuses(self._fresh_step(self.session)))

    def test_writer_succeeds_once_the_lock_is_released(self):
        holder = self.Session()
        holder.query(ResourceWorkflowStep).populate_existing().with_for_update() \
            .filter_by(id=self.step_id).one()
        holder.rollback()
        holder.close()

        session_b = self.Session()
        try:
            helpers.set_step_status(session_b, self._fresh_step(session_b), 'Complete', node_name='node_b')
        finally:
            session_b.close()

        self.session.expire_all()
        self.assertEqual(['Complete'], helpers.get_step_statuses(self._fresh_step(self.session)))

    def test_legacy_mirror_is_persisted_for_rolled_back_code(self):
        session_a = self.Session()
        try:
            helpers.set_step_status(session_a, self._fresh_step(session_a), 'Failed', node_name='node_a')
        finally:
            session_a.close()

        self.session.expire_all()
        mirror = self._fresh_step(self.session).get_attribute(MIRROR)
        self.assertEqual(['Failed'], mirror)


class HelpersArgParseTests(unittest.TestCase):

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
