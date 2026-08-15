import argparse
import logging
import os
import time

from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, PendingRollbackError
from sqlalchemy.orm import sessionmaker

log = logging.getLogger(f'tethys.{__name__}')

# Authoritative store for sub-job statuses: {node_name: status}.
CONDOR_JOB_STATUSES_BY_NODE_KEY = 'condor_job_statuses_by_node'

# A plain list of the same values, written alongside the authoritative store so
# that code predating the per-node store still reads the shape it expects. That
# matters for a rollback: the previous implementation does `statuses.append(...)`
# and tests `STATUS_FAILED in statuses`, both of which misbehave against a dict
# (append raises, and `in` tests keys, so a real failure reports success).
# Read through get_step_statuses() rather than reading this key directly.
#
# COMPAT (added by PR #183, 2026-08-13): this mirror exists only to keep a rollback to
# any release before PR #183 safe. Safe to stop writing it once rolling back that far
# is no longer supported. Note that downstream pins this package by commit SHA rather
# than by tag, so "earlier" is not bounded by the tag history alone.
CONDOR_JOB_STATUSES_KEY = 'condor_job_statuses'

# How long to wait for another node's status write before giving up. Without a
# bound, a node killed by HTCondor between taking the row lock and committing
# blocks every sibling's write until the backend is reaped, which can be minutes.
# Exceeding it raises OperationalError, which set_step_status already retries.
STATUS_LOCK_TIMEOUT_MS = 5000

# Postgres SQLSTATE for "could not obtain lock", which is what lock_timeout raises.
LOCK_NOT_AVAILABLE = '55P03'


@lru_cache(maxsize=1)
def dag_node_name():
    """
    Name of the DAG node this process is running as.

    DAGMan adds ``DAGNodeName`` to the job ad of every node it submits, and
    HTCondor makes the job ad available to the running job in the file named by
    the ``_CONDOR_JOB_AD`` environment variable. Reading it there means a job
    can identify itself without any extra arguments being threaded through.

    The result is cached for the life of the process. A job reports its status
    more than once (see decorators.workflow_step_job), and the fallback below
    embeds the current time, so recomputing it would hand the same node two
    different keys and defeat the point of keying by node.

    Returns:
        str: the node name, or a process-unique placeholder if it cannot be
            determined. The placeholder must be unique: a constant would make
            every node overwrite the same entry.
    """
    job_ad_path = os.environ.get('_CONDOR_JOB_AD')

    if job_ad_path:
        try:
            with open(job_ad_path, 'r') as job_ad:
                for line in job_ad:
                    key, separator, value = line.partition('=')
                    if separator and key.strip() == 'DAGNodeName':
                        name = value.strip().strip('"')
                        if name:
                            return name
            log.warning('No DAGNodeName in job ad %s; falling back to a generated node name.', job_ad_path)
        except OSError:
            log.warning('Could not read job ad %s; falling back to a generated node name.', job_ad_path, exc_info=True)

    # Unique per process, so two nodes never collide, but NOT stable across
    # processes: a node retried on another host cannot overwrite its earlier
    # entry and will leave both behind.
    return 'unknown_{}_{}'.format(os.getpid(), int(time.time()))


def _is_lock_timeout(error):
    """
    Whether an OperationalError is Postgres giving up on a row lock (55P03).

    Contention is not a broken connection, and the two want opposite handling:
    a lock timeout means some other node held the row too long, and the
    connection is still perfectly good.
    """
    return getattr(getattr(error, 'orig', None), 'pgcode', None) == LOCK_NOT_AVAILABLE


@contextmanager
def released_sessions(*sessions):
    """
    Holds no database transaction for the duration of the block.

    A workflow_step_job body opens a transaction as soon as it queries anything,
    and that transaction stays open until the job ends. When the body then does
    something long that needs no database at all -- running GSSHA, publishing
    layers to GeoServer -- the transaction sits idle for the whole of it. Under
    a transaction-mode connection pooler an open transaction pins a server
    connection, so an idle worker occupies a slot that the web application is
    also drawing from.

    Wrap the long stretch in this to commit first and hold nothing while it
    runs::

        with released_sessions(resource_db_session, model_db_session):
            run_gssha(project_dir, project_file)

    Committing rather than rolling back is deliberate: both end the transaction,
    but rolling back would silently discard whatever the body had staged.

    ``expire_on_commit`` is switched off for the sessions given here and
    restored on the way out. Without that, the commit on entry would expire
    every loaded object and the first attribute read after the block would open
    a new transaction, which is most of what the block was avoiding. It is
    applied per-session rather than on the sessionmaker so that callers which
    never use this function keep the default refresh-after-commit behaviour.

    Objects loaded before the block stay readable inside and after it. Anything
    modified after the block should be re-read (``populate_existing()`` or
    ``Session.refresh()``) rather than trusted from the identity map, since it
    may have been changed by another DAG node in the meantime.

    Doing database work inside the block re-opens a transaction and defeats the
    purpose; keep the block to work that needs no session.

    Args:
        *sessions(sqlalchemy.orm.Session): Sessions to release. ``None`` is
            accepted and skipped, because workflow_step_job passes a null model
            database session when the model database URL is not usable.
    """
    unique_sessions = []
    seen = set()

    for session in sessions:
        if session is None or id(session) in seen:
            continue
        seen.add(id(session))
        unique_sessions.append(session)

    expire_on_commit = [(s, s.expire_on_commit) for s in unique_sessions]

    try:
        for session in unique_sessions:
            # Order matters: switching this off after the commit would be too
            # late to stop that commit expiring everything.
            session.expire_on_commit = False
            session.commit()

        yield
    finally:
        for session, previous in expire_on_commit:
            session.expire_on_commit = previous


def set_step_status(resource_db_session, step, status, node_name=None):
    """
    Records the status of one DAG node on the provided step.

    Retries once. A lock timeout is retried on the same session, since the
    connection is healthy and only the row was busy. Anything else is treated as a
    dead connection (the server terminated the backend, the network dropped) and
    recovers by invalidating that connection, opening a fresh session from the same
    engine, and retrying there.

    CAUTION: the dead-connection path calls ``Session.invalidate()``, which discards
    everything uncommitted on that session, not just this write. Commit or flush any
    other pending work before calling this.

    Args:
        resource_db_session(sqlalchemy.orm.Session): Session bound to the step.
        step(ResourceWorkflowStep): The step to modify
        status(str): The status to set.
        node_name(str, optional): Name of the reporting node. Defaults to the
            DAG node name of the running job.
    """
    node_name = node_name or dag_node_name()
    contended = False

    try:
        _record_status(resource_db_session, step, status, node_name)
        return
    except (OperationalError, PendingRollbackError) as e:
        contended = _is_lock_timeout(e)

    if contended:
        # Healthy connection, busy row. Keep the session and try again rather than
        # throwing away a good connection during exactly the contention the row
        # lock is there to create.
        resource_db_session.rollback()
        _record_status(resource_db_session, step, status, node_name)
        return

    # Invalidate the dead connection so the pool evicts it, then retry once
    # on a brand-new session from the same engine.
    resource_db_session.invalidate()
    engine = resource_db_session.get_bind()
    step_cls = type(step)
    step_id = step.id
    fresh_session = sessionmaker(bind=engine)()
    try:
        fresh_step = fresh_session.query(step_cls).get(step_id)
        _record_status(fresh_session, fresh_step, status, node_name)
    finally:
        fresh_session.close()


def _set_lock_timeout(session):
    """
    Bounds how long the row lock in _record_status will be waited for.

    Postgres only; other backends are left at their defaults rather than being
    given a statement they would reject. SET LOCAL applies to the surrounding
    transaction only, so it does not leak to other users of the connection.
    """
    bind = session.get_bind()

    if bind is None or bind.dialect.name != 'postgresql':
        return

    session.execute(text("SET LOCAL lock_timeout = '{}ms'".format(STATUS_LOCK_TIMEOUT_MS)))


def _status_dict(step):
    """
    A step's node statuses as a dict, whatever shape they are stored in.

    Reads the authoritative per-node store when present. Otherwise falls back to
    the shapes written by earlier releases: the original flat list, and the dict
    that a pre-release build of this change wrote under the old key. Entries from
    the flat list carry no node identity, so they are given positional keys.

    Anything else (a string, a number, nothing at all) yields an empty dict
    rather than being coerced, so a corrupt value cannot masquerade as statuses.
    """
    statuses = step.get_attribute(CONDOR_JOB_STATUSES_BY_NODE_KEY)

    if isinstance(statuses, dict):
        return dict(statuses)

    legacy = step.get_attribute(CONDOR_JOB_STATUSES_KEY)

    # COMPAT (added by PR #183, 2026-08-13): a build of this change that shipped before
    # the per-node key existed wrote the dict here instead. Safe to delete once no
    # deployment is running a commit between e37cc4e and this one -- that range was
    # never tagged, so only pinned-by-SHA consumers can be on it.
    if isinstance(legacy, dict):
        return dict(legacy)

    # COMPAT (added by PR #183, 2026-08-13): the flat list written before statuses were
    # keyed by node. Safe to delete once no ResourceWorkflowStep submitted before PR #183
    # shipped can still report -- i.e. once every DAG in flight at that upgrade has
    # finished. Deleting it earlier silently drops those steps' statuses.
    if isinstance(legacy, list):
        if legacy:
            log.warning(
                'Step %s still holds %d status(es) in the pre-node-name format. They cannot be '
                'attributed to a node, so a node that reported before the upgrade and then retries '
                'will leave its earlier status behind.',
                step.id, len(legacy),
            )
        return {'_legacy_{}'.format(i): s for i, s in enumerate(legacy)}

    return {}


def initialize_step_statuses(step):
    """
    Clears a step's node statuses ahead of a new job submission.

    Call this BEFORE the DAG is submitted. Nodes begin reporting as soon as
    DAGMan schedules them, and this write is an unlocked overwrite of the whole
    attributes document, so clearing after submission can discard statuses that
    have already been committed.

    Args:
        step(ResourceWorkflowStep): The step to reset.
    """
    step.set_attribute(CONDOR_JOB_STATUSES_BY_NODE_KEY, {})
    step.set_attribute(CONDOR_JOB_STATUSES_KEY, [])


def _record_status(session, step, status, node_name):
    """
    Writes one node's status into the step, keyed by node name.

    The statuses are stored under a single key of the step's attributes, and
    set_attribute re-serializes the whole attributes document, so this is a
    read-modify-write of one column. Two nodes finishing at the same time would
    otherwise each write their own version and lose the other's status, which
    for a lost failure means the workflow reports success. The row is locked for
    the duration to serialize concurrent nodes.

    Keying by node name also makes a retried node overwrite its own earlier
    status instead of leaving both, so a node that fails and then succeeds does
    not leave a failure behind.

    Both the per-node store and the legacy list mirror are written, so a release
    rolled back to code that predates the per-node store still finds a list.
    """
    _set_lock_timeout(session)

    locked_step = (
        session.query(type(step))
        .populate_existing()
        .with_for_update()
        .filter_by(id=step.id)
        .one()
    )

    statuses = _status_dict(locked_step)
    statuses[node_name] = status

    locked_step.set_attribute(CONDOR_JOB_STATUSES_BY_NODE_KEY, statuses)
    locked_step.set_attribute(CONDOR_JOB_STATUSES_KEY, list(statuses.values()))
    session.commit()


def get_step_statuses(step):
    """
    The statuses reported by a step's DAG nodes.

    Args:
        step(ResourceWorkflowStep): The step to read.

    Returns:
        list: the reported statuses, in whatever shape they are stored.
    """
    return list(_status_dict(step).values())


def parse_workflow_step_args():
    """
    Parses and validates command line arguments for workflow_step_job.
    Returns:
        argparse.Namespace: The parsed and validated arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'resource_db_url',
        help='SQLAlchemy URL to the database containing the Resource and Workflow data.'
    )
    parser.add_argument(
        'model_db_url',
        help='SQLAlchemy URL to the database containing the model data.'
    )
    parser.add_argument(
        'resource_id',
        help='ID of the Resource this job is associated with.'
    )
    parser.add_argument(
        'resource_workflow_id',
        help='ID of the ResourceWorkflow this job is associated with.'
    )
    parser.add_argument(
        'resource_workflow_step_id',
        help='ID of the ResourceWorkflowStep this job is associated with.'
    )
    parser.add_argument(
        'gs_private_url',
        help='Private url to GeoServer.'
    )
    parser.add_argument(
        'gs_public_url',
        help='Public url to GeoServer.'
    )
    parser.add_argument(
        'resource_class',
        help='Dot path to resource class.'
    )
    parser.add_argument(
        'workflow_class',
        help='Dot path to workflow class.'
    )
    parser.add_argument(
        'workflow_params_file',
        help='Path to a file containing the JSON-serialized parameters from the workflow.'
    )
    parser.add_argument(
        '-s', '--scenario_id',
        dest='scenario_id',
        help='Scenario ID for the model.',
        default=1
    )
    parser.add_argument(
        '-a', '--app_namespace',
        help='Namespace of the app the database belongs to.',
        dest='app_namespace',
        default='app'
    )
    args, unknown_args = parser.parse_known_args()
    return args, unknown_args
