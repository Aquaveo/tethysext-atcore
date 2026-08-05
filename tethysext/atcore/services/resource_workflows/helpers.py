import argparse
import os
import time

from sqlalchemy.exc import OperationalError, PendingRollbackError
from sqlalchemy.orm import sessionmaker

CONDOR_JOB_STATUSES_KEY = 'condor_job_statuses'


def dag_node_name():
    """
    Name of the DAG node this process is running as.

    DAGMan adds ``DAGNodeName`` to the job ad of every node it submits, and
    HTCondor makes the job ad available to the running job in the file named by
    the ``_CONDOR_JOB_AD`` environment variable. Reading it there means a job
    can identify itself without any extra arguments being threaded through.

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
        except OSError:
            pass

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
    """
    locked_step = (
        session.query(type(step))
        .populate_existing()
        .with_for_update()
        .filter_by(id=step.id)
        .one()
    )

    statuses = locked_step.get_attribute(CONDOR_JOB_STATUSES_KEY) or {}

    if isinstance(statuses, list):
        # A step that was already running when this was deployed still holds the
        # previous list form.
        statuses = {'_legacy_{}'.format(i): s for i, s in enumerate(statuses)}

    statuses[node_name] = status
    locked_step.set_attribute(CONDOR_JOB_STATUSES_KEY, statuses)
    session.commit()


def get_step_statuses(step):
    """
    The statuses reported by a step's DAG nodes.

    Args:
        step(ResourceWorkflowStep): The step to read.

    Returns:
        list: the reported statuses, from either the current or previous form.
    """
    statuses = step.get_attribute(CONDOR_JOB_STATUSES_KEY) or {}

    if isinstance(statuses, dict):
        return list(statuses.values())

    return list(statuses)


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
