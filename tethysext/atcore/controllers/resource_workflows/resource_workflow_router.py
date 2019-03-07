"""
********************************************************************************
* Name: resource_workflow_view.py
* Author: nswain
* Created On: November 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.shortcuts import redirect, reverse
from django.contrib import messages
from tethys_apps.utilities import get_active_app
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.controllers.resource_workflows.base import AppUsersResourceWorkflowController


class ResourceWorkflowRouter(AppUsersResourceWorkflowController):
    """
    Router for resource workflow views. Routes to appropriate step controller.
    """
    http_method_names = ['get', 'post', 'delete']

    def route_to_step_controller(self, request, resource_id, workflow_id, step_id, *args, **kwargs):
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

        try:
            step = self.get_step(request, step_id)
        except (StatementError, NoResultFound):
            messages.warning(request, 'Invalid step for workflow: {}.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(self.back_url)

        # Validate HTTP method
        if request.method.lower() not in step.http_methods:
            messages.warning(request, 'An unexpected error has occured: '
                                      'Method not allowed ({}).'.format(request.method))
            return redirect(self.back_url)

        controller = step.get_controller(
            _app=self._app,
            _AppUser=self._AppUser,
            _Organization=self._Organization,
            _Resource=self._Resource,
            _PermissionsManager=self._PermissionsManager,
            _persistent_store_name=self._persistent_store_name,
            _ResourceWorkflow=self._ResourceWorkflow,
            _ResourceWorkflowStep=self._ResourceWorkflowStep
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

    def get(self, request, resource_id, workflow_id, step_id=None, *args, **kwargs):
        """
        Route GET requests.
        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        if not step_id:
            _ResourceWorkflow = self.get_resource_workflow_model()
            session = None

            try:
                make_session = self.get_sessionmaker()
                session = make_session()
                workflow = self.get_workflow(request, workflow_id, session=session)

                # Get step to render
                _, step = workflow.get_next_step()

                # Get step id
                step_id = step.id if step else None

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

            if not step_id:
                messages.warning(request, 'Could not identify next step.')
                return redirect(self.back_url)

            # Redirect to next step page
            active_app = get_active_app(request)
            app_namespace = active_app.namespace
            url_name = '{}:{}_workflow_step'.format(app_namespace, _ResourceWorkflow.TYPE)
            return redirect(
                reverse(url_name, kwargs={'resource_id': resource_id, 'workflow_id': workflow_id, 'step_id': step_id})
            )

        response = self.route_to_step_controller(
            request=request,
            resource_id=resource_id,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        return response

    def post(self, request, resource_id, workflow_id, step_id, *args, **kwargs):
        """
        Route POST requests.
        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        response = self.route_to_step_controller(
            request=request,
            resource_id=resource_id,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        return response

    def delete(self, request, resource_id, workflow_id, step_id, *args, **kwargs):
        """
        Route DELETE requests.
        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        response = self.route_to_step_controller(
            request=request,
            resource_id=resource_id,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        return response
