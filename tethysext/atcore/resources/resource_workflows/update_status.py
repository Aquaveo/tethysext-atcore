#!/opt/tethys-python
"""
********************************************************************************
* Name: update_status.py
* Author: nswain
* Created On: April 22, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from tethysext.atcore.services.resource_workflows.helpers import parse_workflow_step_args
# DO NOT REMOVE, need to import all the subclasses of ResourceWorkflowStep for the polymorphism to work.
from tethysext.atcore.models.resource_workflow_steps import *  # noqa: F401, F403


def main(args):
    print('Given Arguments:')
    print(str(args))

    # Session vars
    step = None
    model_db_session = None
    resource_db_session = None

    # Write out needed files
    try:
        # Get the resource database session
        resource_db_engine = create_engine(args.resource_db_url)
        make_resource_db_session = sessionmaker(bind=resource_db_engine)
        resource_db_session = make_resource_db_session()

        # Get the step
        # NOTE: if you get an error related to polymorphic_identity not being found, it may be caused by import
        # errors with a subclass of the ResourceWorkflowStep. It could also be caused indirectly if the subclass
        # has Pickle typed columns with values that import things.
        step = resource_db_session.query(ResourceWorkflowStep).get(args.resource_workflow_step_id)

        print('Updating status...')
        job_statuses = step.get_attribute('condor_job_statuses')
        print(job_statuses)
        if step.STATUS_FAILED in job_statuses:
            step.set_status(step.ROOT_STATUS_KEY, step.STATUS_FAILED)
        else:
            step.set_status(step.ROOT_STATUS_KEY, step.STATUS_COMPLETE)

        resource_db_session.commit()

    except Exception as e:
        if step and resource_db_session:
            step.set_status(step.ROOT_STATUS_KEY, step.STATUS_FAILED)
            resource_db_session.commit()
        sys.stderr.write('Error processing {0}'.format(args.resource_workflow_step_id))
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write(repr(e))
        sys.stderr.write(str(e))
    finally:
        lock_on_complete = step.options.get('lock_on_complete', None)
        unlock_on_complete = step.options.get('unlock_on_complete', None)

        if lock_on_complete and unlock_on_complete:
            raise RuntimeError('Improperly configured SpatialCondorJobRWS: lock_on_complete and unlock_on_complete '
                               'options are both set to True')

        if lock_on_complete is True:
            # Lock the resource
            if step.options.get('resource_lock_required'):
                raise ValueError('Acquiring resource locks on completion of jobs is not supported at this time.')
                # Cannot load Resource subclasses b/c of polymorphic discriminator issues...
                # step.acquire_lock_and_log(None, model_db_session, resource)

            # Lock the workflow
            elif step.options.get('workflow_lock_required'):
                step.acquire_lock_and_log(None, model_db_session, step.workflow)

        elif unlock_on_complete is True:
            # Unlock the resource
            if step.options.get('resource_lock_required'):
                raise ValueError('Releasing resource locks on completion of jobs is not supported at this time.')
                # Cannot load Resource subclasses b/c of polymorphic discriminator issues...
                # step.release_lock_and_log(None, model_db_session, resource)

            # Unlock the workflow
            elif step.options.get('workflow_lock_required'):
                step.release_lock_and_log(None, model_db_session, step.workflow)

        model_db_session and model_db_session.close()
        resource_db_session and resource_db_session.close()

    print('Updating Status Complete')


if __name__ == '__main__':
    args = parse_workflow_step_args()
    main(args)
