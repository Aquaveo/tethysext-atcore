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
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job


@workflow_step_job
def main(resource_db_session, model_db_session, resource, workflow, step, gs_private_url, gs_public_url, resource_class,
         workflow_class, params_json, params_file, cmd_args):
    print('Given Arguments:')
    print(str(cmd_args))

    # Write out needed files
    try:
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
        sys.stderr.write('Error processing step {0}'.format(cmd_args.resource_workflow_step_id))
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write(repr(e))
        sys.stderr.write(str(e))
    finally:
        try:
            lock_resource_on_complete = step.options.get('lock_resource_on_job_complete', None)
            lock_workflow_on_complete = step.options.get('lock_workflow_on_job_complete', None)
            unlock_resource_on_complete = step.options.get('unlock_resource_on_job_complete', None)
            unlock_workflow_on_complete = step.options.get('unlock_workflow_on_job_complete', None)

            if lock_resource_on_complete and unlock_resource_on_complete:
                raise RuntimeError('Improperly configured SpatialCondorJobRWS: lock_resource_on_complete and '
                                   'unlock_resource_on_complete options are both enabled.')

            if lock_workflow_on_complete and unlock_workflow_on_complete:
                raise RuntimeError('Improperly configured SpatialCondorJobRWS: lock_workflow_on_complete and '
                                   'unlock_workflow_on_complete options are both enabled.')

            if lock_resource_on_complete is True:
                raise ValueError('Acquiring resource locks on completion of jobs is not supported at this time.')
                # Cannot load Resource subclasses b/c of polymorphic discriminator issues...
                # resource.acquire_user_lock()

            if lock_workflow_on_complete:
                step.workflow.acquire_user_lock()

            if unlock_resource_on_complete:
                raise ValueError('Releasing resource locks on completion of jobs is not supported at this time.')
                # Cannot load Resource subclasses b/c of polymorphic discriminator issues...
                # resource.release_user_lock()

            if unlock_workflow_on_complete:
                step.workflow.release_user_lock()

            model_db_session and model_db_session.commit()
            resource_db_session and resource_db_session.commit()

        except Exception as e:
            sys.stderr.write('Error processing locks after processing step {0}'
                             .format(cmd_args.resource_workflow_step_id))
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write(repr(e))
            sys.stderr.write(str(e))

    print('Updating Status Complete')
