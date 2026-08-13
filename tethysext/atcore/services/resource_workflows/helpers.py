import argparse
import logging
import os
import time

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
# COMPAT (added 1.16.3, 2026-08-13): this mirror exists only to keep a rollback to
# 1.16.2 or earlier safe. Safe to stop writing it once rolling back that far is no
# longer supported. Note that downstream pins this package by commit SHA rather
# than by tag, so "earlier" is not bounded by the tag history alone.
CONDOR_JOB_STATUSES_KEY = 'condor_job_statuses'

# How long to wait for another node's status write before giving up. Without a
# bound, a node killed by HTCondor between taking the row lock and committing
# blocks every sibling's write until the backend is reaped, which can be minutes.
# Exceeding it raises OperationalError, which set_step_status already retries.
STATUS_LOCK_TIMEOUT_MS = 5000


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


def set_step_status(resource_db_session, step, status, node_name=None):
    """
    Records the status of one DAG node on the provided step.

    Recovers once from a dead connection (e.g., the server terminated the
    backend, the network dropped) by invalidating the bad connection,
    opening a fresh session from the same engine, and retrying the write.

    Args:
        resource_db_session(sqlalchemy.orm.Session): Session bound to the step.
        step(ResourceWorkflowStep): The step to modify
        status(str): The status to set.
        node_name(str, optional): Name of the reporting node. Defaults to the
            DAG node name of the running job.
    """
    node_name = node_name or dag_node_name()

    try:
        _record_status(resource_db_session, step, status, node_name)
        return
    except (OperationalError, PendingRollbackError):
        pass

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

    # COMPAT (added 1.16.3, 2026-08-13): a build of this change that shipped before
    # the per-node key existed wrote the dict here instead. Safe to delete once no
    # deployment is running a commit between e37cc4e and this one -- that range was
    # never tagged, so only pinned-by-SHA consumers can be on it.
    if isinstance(legacy, dict):
        return dict(legacy)

    # COMPAT (added 1.16.3, 2026-08-13): the flat list written before statuses were
    # keyed by node. Safe to delete once no ResourceWorkflowStep submitted before
    # 1.16.3 can still report -- i.e. once every DAG in flight at that upgrade has
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
