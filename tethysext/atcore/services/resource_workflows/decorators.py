import sys
import json
import logging
import traceback
from pprint import pprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import StatementError, ArgumentError
from sqlalchemy.orm.exc import NoResultFound
from django.http import JsonResponse
from django.utils.functional import wraps
from django.shortcuts import redirect
from django.contrib import messages
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.services.resource_workflows.helpers import set_step_status, parse_workflow_step_args
from tethysext.atcore.utilities import clean_request, import_from_string
from tethysext.atcore.models.app_users import ResourceWorkflowStep
# DO NOT REMOVE, need to import all the subclasses of ResourceWorkflowStep for the polymorphism to work.
from tethysext.atcore.models.resource_workflow_steps import *  # noqa: F401, F403
from tethysext.atcore.models.resource_workflow_results import *  # noqa: F401, F403
# END DO NOT REMOVE


log = logging.getLogger(f'tethys.{__name__}')


def workflow_step_controller(is_rest_controller=False):
    def decorator(controller_func):
        def _wrapped_controller(self, request, workflow_id, step_id, back_url=None, resource_id=None,
                                resource=None, session=None, *args, **kwargs):
            _ResourceWorkflow = self.get_resource_workflow_model()
            # Defer to outer scope if session is given
            manage_session = session is None
            current_step = None

            try:
                if manage_session:
                    make_session = self.get_sessionmaker()
                    session = make_session()

                # Assign the resource id if resource given
                if resource and not resource_id:
                    resource_id = resource.id

                # Handle case when resource is not given but resource_id is
                if not resource and resource_id:
                    resource = self.get_resource(request, resource_id=resource_id, session=session)

                workflow = self.get_workflow(request, workflow_id=workflow_id, session=session)
                current_step = self.get_step(request, step_id=step_id, session=session)

                # Call the Controller
                return controller_func(self, request, session, resource, workflow, current_step, back_url,
                                       *args, **kwargs)

            except (StatementError, NoResultFound) as e:
                messages.warning(request, 'The {} could not be found.'.format(
                    _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
                ))
                if not is_rest_controller:
                    return redirect(self.back_url)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            except ATCoreException as e:
                error_message = str(e)
                messages.warning(request, error_message)
                if not is_rest_controller:
                    return redirect(self.back_url)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            except ValueError as e:
                if session:
                    session.rollback()
                    # Save error message to display to the user
                    if current_step:
                        current_step.set_attribute(current_step.ATTR_STATUS_MESSAGE, str(e))
                        current_step.set_status(current_step.ROOT_STATUS_KEY, current_step.STATUS_ERROR)
                        session.commit()

                if not is_rest_controller:
                    # Remove method so we redirect to the primary GET page...
                    c_request = clean_request(request)
                    return self.get(c_request, resource_id=resource_id, workflow_id=workflow_id, step_id=step_id)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            except RuntimeError as e:
                if session:
                    session.rollback()
                    # Save error message to display to the user
                    if current_step:
                        current_step.set_status(current_step.ROOT_STATUS_KEY, current_step.STATUS_ERROR)
                        session.commit()

                messages.error(request, "We're sorry, an unexpected error has occurred.")
                log.exception(e)
                if not is_rest_controller:
                    # Remove method so we redirect to the primary GET page...
                    c_request = clean_request(request)
                    return self.get(c_request, resource_id=resource_id, workflow_id=workflow_id, step_id=step_id)

                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            finally:
                session and manage_session and session.close()

        return wraps(controller_func)(_wrapped_controller)
    return decorator


def workflow_step_job(job_func=None, *, db_engine_kwargs=None):
    def decorator(inner_job_func):
        def _wrapped():
            if inner_job_func.__module__ == '__main__':
                args, unknown_args = parse_workflow_step_args()

                print('Given Arguments:')
                print(str(args))

                # Session vars
                step = None
                model_db_engine = None
                model_db_session = None
                resource_db_session = None
                ret_val = None

                def record_status(status):
                    """
                    Records this node's status, never raising.

                    set_step_status already retries a busy row and a dead connection.
                    This adds the last resort: if the caller's session cannot be used at
                    all, try once on a brand-new session from the same engine, and if
                    even that fails, say so through the logger rather than only on
                    stderr -- a status that never lands is the silent failure this whole
                    mechanism exists to prevent, so it needs somewhere an operator can
                    actually see it.
                    """
                    try:
                        set_step_status(resource_db_session, step, status)
                        return
                    except Exception:
                        log.warning(
                            'Could not record %s for step %s on the job session; retrying on a fresh one.',
                            status, args.resource_workflow_step_id, exc_info=True,
                        )

                    try:
                        retry_session = sessionmaker(bind=resource_db_engine)()
                        try:
                            retry_step = retry_session.query(type(step)).get(step.id)
                            set_step_status(retry_session, retry_step, status)
                        finally:
                            retry_session.close()
                    except Exception:
                        log.error(
                            'Could not record %s for step %s. The status is lost; the workflow will '
                            'not reflect what this node did.',
                            status, args.resource_workflow_step_id, exc_info=True,
                        )
                        traceback.print_exc(file=sys.stderr)

                try:
                    # Get the resource database session
                    engine_kwargs = db_engine_kwargs if db_engine_kwargs else {}
                    resource_db_engine = create_engine(args.resource_db_url, **engine_kwargs)
                    make_resource_db_session = sessionmaker(bind=resource_db_engine)
                    resource_db_session = make_resource_db_session()

                    try:
                        model_db_engine = create_engine(args.model_db_url, **engine_kwargs)
                        make_model_db_session = sessionmaker(bind=model_db_engine)
                        model_db_session = make_model_db_session()
                    except ArgumentError:
                        sys.stderr.write(repr('invalid model_db_url'))

                    # Import Resource and Workflow Classes
                    ResourceClass = import_from_string(args.resource_class)
                    WorkflowClass = import_from_string(args.workflow_class)

                    # Get the step
                    # NOTE: if you get an error related to polymorphic_identity
                    # not being found, it may be caused by import
                    # errors with a subclass of the ResourceWorkflowStep.
                    # It could also be caused indirectly if the subclass
                    # has Pickle typed columns with values that import things.
                    step = resource_db_session.query(ResourceWorkflowStep).get(args.resource_workflow_step_id)

                    # IMPORTANT: External Resource classes need to be imported at the top of the job file to
                    # allow sqlalchemy to resolve the polymorphic identity.
                    resource = resource_db_session.query(ResourceClass).get(args.resource_id)

                    # Process parameters from workflow steps
                    with open(args.workflow_params_file, 'r') as p:
                        params_json = json.loads(p.read())

                    print('Workflow Parameters:')
                    pprint(params_json)

                    ret_val = inner_job_func(
                        resource_db_session=resource_db_session,
                        model_db_session=model_db_session,
                        resource=resource,
                        workflow=step.workflow,
                        step=step,
                        gs_private_url=args.gs_private_url,
                        gs_public_url=args.gs_public_url,
                        resource_class=ResourceClass,
                        workflow_class=WorkflowClass,
                        params_json=params_json,
                        params_file=args.workflow_params_file,
                        cmd_args=args,
                        extra_args=unknown_args
                    )

                    # Update step status
                    #
                    # Deliberately guarded separately from the work above. The work has
                    # already succeeded at this point, so a failure to record that must
                    # not fall through to the handler below and be written down as a node
                    # failure -- with the row lock the status write now takes, contention
                    # is a real way for this to fail.
                    print('Updating status...')
                    record_status(step.STATUS_COMPLETE)

                except Exception as e:
                    if step and resource_db_session:
                        record_status(step.STATUS_FAILED)
                    sys.stderr.write('Error processing {0}'.format(args.resource_workflow_step_id))
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.write(repr(e))
                    sys.stderr.write(str(e))

                finally:
                    print('Closing sessions...')
                    model_db_session and model_db_session.close()
                    resource_db_session and resource_db_session.close()

                print('Processing Complete')
                return ret_val

        return _wrapped()
    # Support usage with and without parentheses: @workflow_step_job and @workflow_step_job(...)
    if callable(job_func):
        return decorator(job_func)
    return decorator
