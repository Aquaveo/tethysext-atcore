"""
********************************************************************************
* Name: resource_workflow_view.py
* Author: nswain
* Created On: November 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import logging
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.shortcuts import redirect, reverse
from django.contrib import messages
from tethys_apps.utilities import get_active_app
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.controllers.resource_workflows.mixins import WorkflowViewMixin
from tethysext.atcore.models.resource_workflow_steps import ResultsResourceWorkflowStep


log = logging.getLogger(__name__)


class ResourceWorkflowRouter(WorkflowViewMixin):
    """
    Router for resource workflow views. Routes to appropriate step controller.
    """
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get', 'post', 'delete']

    def get(self, request, resource_id, workflow_id, step_id=None, result_id=None, *args, **kwargs):
        """
        Route GET requests.

        Controller for the following url patterns:

        /resource/<resource_id>/my-custom-workflow/<workflow_id>/
        /resource/<resource_id>/my-custom-workflow/<workflow_id>/step/<step_id>/
        /resource/<resource_id>/my-custom-workflow/<workflow_id>/step/<step_id>/result/<result_id>/

        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render. Optional. Required if result_id given.
            result_id(str): ID of the result to render. Optional.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        step_id_given = step_id is not None
        result_id_given = result_id is not None

        _ResourceWorkflow = self.get_resource_workflow_model()
        session = None

        try:
            make_session = self.get_sessionmaker()
            session = make_session()
            workflow = self.get_workflow(request, workflow_id, session=session)

            if not step_id_given:
                _, step = workflow.get_next_step()
                # Get step id
                step_id = step.id if step else None

                if not step_id:
                    messages.warning(request, 'Could not identify next step.')
                    return redirect(self.back_url)
            else:
                step = self.get_step(request, step_id, session)

            # Determine if step is result step
            is_result_step = isinstance(step, ResultsResourceWorkflowStep)

            # Handle result steps
            if is_result_step and not result_id_given:
                result = step.get_last_result()
                result_id = str(result.id) if result else None

                if not result_id:
                    messages.warning(request, 'Could not identify a result.')
                    return redirect(self.back_url)

            # If any of the required ids were not given originally, redirect to the appropriate url with derived ids
            active_app = get_active_app(request)
            app_namespace = active_app.namespace
            url_kwargs = {'resource_id': resource_id, 'workflow_id': workflow_id, 'step_id': step_id}
            if is_result_step and not result_id_given:
                # Redirect to the result page
                url_name = '{}:{}_workflow_step_result'.format(app_namespace, _ResourceWorkflow.TYPE)
                url_kwargs.update({'result_id': result_id})
                return redirect(reverse(url_name, kwargs=url_kwargs))

            elif not is_result_step and not step_id_given:
                # Redirect to next step page
                url_name = '{}:{}_workflow_step'.format(app_namespace, _ResourceWorkflow.TYPE)
                return redirect(reverse(url_name, kwargs=url_kwargs))

        except (StatementError, NoResultFound):
            messages.warning(request, 'The {} could not be found.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(self.back_url)
        finally:
            session and session.close()

        response = self._get_response(request, resource_id, workflow_id, step_id, result_id, args, kwargs)

        return response

    def post(self, request, resource_id, workflow_id, step_id, result_id=None, *args, **kwargs):
        """
        Route POST requests.
        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            result_id(str): ID of the result to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        response = self._get_response(request, resource_id, workflow_id, step_id, result_id, args, kwargs)

        return response

    def delete(self, request, resource_id, workflow_id, step_id, result_id=None, *args, **kwargs):
        """
        Route DELETE requests.
        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            result_id(str): ID of the result to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        response = self._get_response(request, resource_id, workflow_id, step_id, result_id, args, kwargs)

        return response

    def _get_response(self, request, resource_id, workflow_id, step_id, result_id, args, kwargs):
        """
        Get controller from step or result that will handle the request.

        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            result_id(str): ID of the result to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        if result_id:
            response = self._route_to_result_controller(
                request=request,
                resource_id=resource_id,
                workflow_id=workflow_id,
                step_id=step_id,
                result_id=result_id,
                *args, **kwargs
            )

        else:
            response = self._route_to_step_controller(
                request=request,
                resource_id=resource_id,
                workflow_id=workflow_id,
                step_id=step_id,
                *args, **kwargs
            )
        return response

    def _route_to_step_controller(self, request, resource_id, workflow_id, step_id, *args, **kwargs):
        """
        Get controller from step that will handle the request.

        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        _ResourceWorkflow = self.get_resource_workflow_model()
        session = None

        try:
            make_session = self.get_sessionmaker()
            session = make_session()
            step = self.get_step(request, step_id, session=session)

            # Validate HTTP method
            if request.method.lower() not in step.controller.http_methods:
                raise RuntimeError('An unexpected error has occurred: Method not allowed ({}).'.format(request.method))

            controller = step.controller.instantiate(
                _app=self._app,
                _AppUser=self._AppUser,
                _Organization=self._Organization,
                _Resource=self._Resource,
                _PermissionsManager=self._PermissionsManager,
                _persistent_store_name=self._persistent_store_name,
                _ResourceWorkflow=self._ResourceWorkflow,
                _ResourceWorkflowStep=self._ResourceWorkflowStep,
                base_template=self.base_template
            )

            response = controller(
                request=request,
                resource_id=resource_id,
                workflow_id=workflow_id,
                step_id=step_id,
                back_url=self.back_url,
                *args, **kwargs
            )

            return response

        except (StatementError, NoResultFound):
            messages.warning(request, 'Invalid step for workflow: {}.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(self.back_url)
        finally:
            session and session.close()

    def _route_to_result_controller(self, request, resource_id, workflow_id, step_id, result_id, *args, **kwargs):
        """
        Get controller from result that will handle the request.

        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            result_id(str): ID of the result to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        _ResourceWorkflow = self.get_resource_workflow_model()
        session = None

        try:
            make_session = self.get_sessionmaker()
            session = make_session()
            step = self.get_step(request, step_id, session=session)

            # Check if step is ResultsResourceWorkflowStep
            if not isinstance(step, ResultsResourceWorkflowStep):
                raise RuntimeError('Step must be a ResultsResourceWorkflowStep.')

            # Get the result from the step
            result = step.get_result(result_id=result_id)

            # Validate HTTP method
            if not result:
                messages.error(request, 'Result not found.')
                return redirect(self.back_url)

            if request.method.lower() not in result.controller.http_methods:
                raise RuntimeError('An unexpected error has occurred: Method not allowed ({}).'.format(request.method))

            controller = result.controller.instantiate(
                _app=self._app,
                _AppUser=self._AppUser,
                _Organization=self._Organization,
                _Resource=self._Resource,
                _PermissionsManager=self._PermissionsManager,
                _persistent_store_name=self._persistent_store_name,
                _ResourceWorkflow=self._ResourceWorkflow,
                _ResourceWorkflowStep=self._ResourceWorkflowStep,
                base_template=self.base_template
            )

            response = controller(
                request=request,
                resource_id=resource_id,
                workflow_id=workflow_id,
                step_id=step_id,
                result_id=result_id,
                back_url=self.back_url,
                *args, **kwargs
            )

            return response

        except (StatementError, NoResultFound):
            messages.warning(request, 'Invalid step for workflow: {}.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(self.back_url)
        finally:
            session and session.close()
