import logging
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.http import JsonResponse
from django.utils.functional import wraps
from django.shortcuts import redirect
from django.contrib import messages
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.utilities import clean_request

log = logging.getLogger(__name__)


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
