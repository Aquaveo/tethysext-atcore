import argparse

from sqlalchemy.exc import OperationalError, PendingRollbackError
from sqlalchemy.orm import sessionmaker


def set_step_status(resource_db_session, step, status):
    """
    Sets the status on the provided step to the provided status.

    Recovers once from a dead connection (e.g., the server terminated the
    backend, the network dropped) by invalidating the bad connection,
    opening a fresh session from the same engine, and retrying the write.

    Args:
        resource_db_session(sqlalchemy.orm.Session): Session bound to the step.
        step(ResourceWorkflowStep): The step to modify
        status(str): The status to set.
    """
    try:
        _append_status(resource_db_session, step, status)
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
        _append_status(fresh_session, fresh_step, status)
    finally:
        fresh_session.close()


def _append_status(session, step, status):
    session.refresh(step)
    step_statuses = step.get_attribute('condor_job_statuses')
    step_statuses.append(status)
    step.set_attribute('condor_job_statuses', step_statuses)
    session.commit()


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
