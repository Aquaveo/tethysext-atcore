import argparse


def set_step_status(resource_db_session, step, status):
    """
    Sets the status on the provided step to the provided status.
    Args:
        resource_db_session(sqlalchemy.orm.Session): Session bound to the step.
        step(ResourceWorkflowStep): The step to modify
        status(str): The status to set.
    """
    resource_db_session.refresh(step)
    step_statuses = step.get_attribute('condor_job_statuses')
    step_statuses.append(status)
    step.set_attribute('condor_job_statuses', step_statuses)
    resource_db_session.commit()


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
        help='SQLAlchemy URL to the database containing the GSSHA model.'
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
        'workflow_params_file',
        help='Path to a file containing the JSON-serialized parameters from the workflow.'
    )
    # TODO: Pass in paths to workflow and resource classes so they can be imported dynamically?
    parser.add_argument(
        '-s', '--scenario_id',
        dest='scenario_id',
        help='Scenario ID for this GSSHA model.',
        default=1
    )
    parser.add_argument(
        '-a', '--app_namespace',
        help='Namespace of the app the database belongs to.',
        dest='app_namespace',
        default='agwa'
    )
    args = parser.parse_args()
    return args
