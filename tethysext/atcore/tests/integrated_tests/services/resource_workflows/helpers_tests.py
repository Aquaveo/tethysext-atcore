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
from sqlalchemy import create_engine, inspect
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


class ReleasedSessionsTests(unittest.TestCase):
    """
    Exercises released_sessions against a real database.

    Whether a transaction is actually open, and whether a commit expires loaded
    objects, are properties of the session and the server rather than of the
    call sequence, so mocks cannot show either.
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
        self.workflow = ResourceWorkflow(name='release_test')
        self.step = ResourceWorkflowStep(name='release_step', help='h', order=1)
        self.step.attributes = {STATUSES: {}}
        self.workflow.steps = [self.step]
        self.session.add(self.workflow)
        self.session.commit()
        self.step_id = self.step.id
        self.workflow_id = self.workflow.id

    def tearDown(self):
        self.session.rollback()
        self.session.delete(self.session.query(ResourceWorkflow).get(self.workflow_id))
        self.session.commit()
        self.session.close()

    def _load_step(self, session):
        return session.query(ResourceWorkflowStep).get(self.step_id)

    def test_no_transaction_is_held_inside_the_region(self):
        """The whole point: a long region must not pin a server connection."""
        session = self.Session()
        try:
            self._load_step(session)
            self.assertTrue(session.in_transaction())

            with helpers.released_sessions(session):
                self.assertFalse(session.in_transaction())
        finally:
            session.close()

    def test_loaded_attributes_survive_the_release(self):
        session = self.Session()
        try:
            step = self._load_step(session)
            self.assertEqual('release_step', step.name)

            with helpers.released_sessions(session):
                self.assertFalse(inspect(step).expired)
                self.assertEqual('release_step', step.name)
                self.assertFalse(session.in_transaction())
        finally:
            session.close()

    def test_relationship_traversal_survives_the_release(self):
        """The decorator traverses step.workflow before the body and uses step after it."""
        session = self.Session()
        try:
            step = self._load_step(session)
            self.assertIsNotNone(step.workflow)

            with helpers.released_sessions(session):
                pass

            self.assertEqual(self.workflow_id, step.workflow.id)
        finally:
            session.close()

    def test_expire_on_commit_is_restored_on_exit(self):
        session = self.Session()
        try:
            self.assertTrue(session.expire_on_commit)
            with helpers.released_sessions(session):
                self.assertFalse(session.expire_on_commit)
            self.assertTrue(session.expire_on_commit)
        finally:
            session.close()

    def test_expire_on_commit_is_restored_when_the_body_raises(self):
        session = self.Session()
        try:
            with self.assertRaises(RuntimeError):
                with helpers.released_sessions(session):
                    raise RuntimeError('gssha failed')
            self.assertTrue(session.expire_on_commit)
        finally:
            session.close()

    def test_non_adopting_sessions_keep_expire_on_commit(self):
        """R7: a session never handed to the seam must keep default refresh-after-commit."""
        adopting = self.Session()
        untouched = self.Session()
        try:
            step = self._load_step(untouched)
            self.assertEqual('release_step', step.name)

            with helpers.released_sessions(adopting):
                pass

            self.assertTrue(untouched.expire_on_commit)
            untouched.commit()
            self.assertTrue(inspect(step).expired)
        finally:
            adopting.close()
            untouched.close()

    def test_status_write_after_a_release_still_commits(self):
        session = self.Session()
        try:
            step = self._load_step(session)

            with helpers.released_sessions(session):
                pass

            helpers.set_step_status(session, step, 'Complete', node_name=NODE)
        finally:
            session.close()

        self.session.expire_all()
        self.assertEqual(['Complete'], helpers.get_step_statuses(self._load_step(self.session)))

    def test_pending_write_is_committed_not_discarded(self):
        """commit() rather than rollback(): staged work must survive the release."""
        session = self.Session()
        try:
            step = self._load_step(session)
            step.set_attribute('released_marker', 'kept')

            with helpers.released_sessions(session):
                pass
        finally:
            session.close()

        self.session.expire_all()
        self.assertEqual('kept', self._load_step(self.session).get_attribute('released_marker'))

    def test_release_is_idempotent(self):
        session = self.Session()
        try:
            self._load_step(session)
            with helpers.released_sessions(session):
                with helpers.released_sessions(session):
                    self.assertFalse(session.in_transaction())
                self.assertFalse(session.expire_on_commit)
            self.assertTrue(session.expire_on_commit)
        finally:
            session.close()

    def test_the_same_session_passed_twice_is_restored(self):
        session = self.Session()
        try:
            with helpers.released_sessions(session, session):
                self.assertFalse(session.expire_on_commit)
            self.assertTrue(session.expire_on_commit)
        finally:
            session.close()


class ReleasedSessionsNilPathTests(unittest.TestCase):
    """The decorator passes model_db_session=None when model_db_url is invalid."""

    def test_none_session_is_skipped(self):
        with helpers.released_sessions(None):
            pass

    def test_no_sessions_is_a_no_op(self):
        with helpers.released_sessions():
            pass

    def test_none_alongside_a_real_session(self):
        session = mock.MagicMock()
        session.expire_on_commit = True

        with helpers.released_sessions(None, session):
            pass

        session.commit.assert_called_once()


class ReleasedSessionsAfterTheBlockTests(unittest.TestCase):
    """
    What a job body may and may not trust once a release has happened.

    Two AGWA scenario scripts reach a sibling step through the workflow after
    running GSSHA and write to it. These pin the contract those scripts rely on.
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
        self.workflow = ResourceWorkflow(name='after_block_test')
        self.target = ResourceWorkflowStep(name='Define Upstream Cells', help='h', order=1)
        self.runner = ResourceWorkflowStep(name='Run', help='h', order=2)
        self.target.attributes = {'imagery': []}
        self.workflow.steps = [self.target, self.runner]
        self.session.add(self.workflow)
        self.session.commit()
        self.workflow_id = self.workflow.id
        self.target_id = self.target.id

    def tearDown(self):
        self.session.rollback()
        self.session.delete(self.session.query(ResourceWorkflow).get(self.workflow_id))
        self.session.commit()
        self.session.close()

    def test_sibling_step_reached_after_a_release_can_be_written(self):
        """The shape both scripts use: traverse to another step, set an attribute, commit."""
        session = self.Session()
        try:
            workflow = session.query(ResourceWorkflow).get(self.workflow_id)

            with helpers.released_sessions(session):
                pass

            step = workflow.get_step_by_name('Define Upstream Cells')
            step.set_attribute('imagery', [{'layer_name': 'agwa:flow_accumulation'}])
            session.commit()
        finally:
            session.close()

        self.session.expire_all()
        written = self.session.query(ResourceWorkflowStep).get(self.target_id)
        self.assertEqual([{'layer_name': 'agwa:flow_accumulation'}], written.get_attribute('imagery'))

    def test_a_read_after_a_release_can_be_stale_unless_refreshed(self):
        """
        Why anything modified after a release must be re-read.

        The object was loaded before the release, so it is still in the identity
        map afterwards. A sibling DAG node committing in between is invisible
        until the row is read again, and a read-modify-write on the stale value
        would drop the sibling's entry.
        """
        reader = self.Session()
        writer = self.Session()
        try:
            step = reader.query(ResourceWorkflowStep).get(self.target_id)
            self.assertEqual([], step.get_attribute('imagery'))

            with helpers.released_sessions(reader):
                pass

            sibling = writer.query(ResourceWorkflowStep).get(self.target_id)
            sibling.set_attribute('imagery', [{'layer_name': 'from_sibling'}])
            writer.commit()

            self.assertEqual([], step.get_attribute('imagery'))

            refreshed = (
                reader.query(ResourceWorkflowStep)
                .populate_existing()
                .filter_by(id=self.target_id)
                .one()
            )
            self.assertEqual([{'layer_name': 'from_sibling'}], refreshed.get_attribute('imagery'))
        finally:
            reader.close()
            writer.close()
