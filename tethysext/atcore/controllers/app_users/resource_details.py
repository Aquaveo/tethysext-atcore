"""
********************************************************************************
* Name: resource_details.py
* Author: nswain
* Created On: April 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Python
from abc import abstractmethod
import logging

# Django
from django.contrib import messages
from django.shortcuts import render, reverse
from django.http import JsonResponse
# Tethys core
from tethys_sdk.permissions import permission_required
from tethys_apps.utilities import get_active_app
# ATCore
from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required, resource_controller

log = logging.getLogger('tethys.' + __name__)


class ResourceDetails(ResourceViewMixin):
    """
    Controller for resource_details page.

    GET: Render detail view of given resource.
    """
    template_name = 'atcore/app_users/resource_details.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get']
    resource_workflows = None

    @abstractmethod
    def get_map_manager(self):
        """
        Map manager for resource
        """
        pass

    @abstractmethod
    def get_spatial_manager(self):
        """
        Get model spatial manager
        """
        pass

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request, *args, **kwargs)

    @active_user_required()
    @permission_required('view_resources')
    @resource_controller()
    def _handle_get(self, request, session, resource, back_url, *args, **kwargs):
        """
        Handle get requests.
        """
        context = {
            'resource': resource,
            'back_url': self.back_url,
            'base_template': self.base_template
        }

        context = self.get_context(request, context)

        return render(request, self.template_name, context)

    def default_back_url(self, request, *args, **kwargs):
        """
        Derive the back controller.

        Args:
            request: Django HttpRequest.

        Returns:
            str: name of the controller to return to when hitting back or on error.
        """
        # Process next
        back_arg = request.GET.get('back', "")
        active_app = get_active_app(request)
        app_namespace = active_app.namespace
        if back_arg == 'manage-organizations':
            back_controller = '{}:app_users_manage_organizations'.format(app_namespace)
        else:
            back_controller = '{}:app_users_manage_resources'.format(app_namespace)
        return reverse(back_controller)

    def get_context(self, request, context):
        """
        Hook for modifying context.

        Args:
            request(HttpRequest): Django HttpRequest.
            context(dict): context object.

        Returns:
            dict: context
        """
        if self.resource_workflows is not None:
            context.update({'workflow_types': self.resource_workflows})
        return context

    def post(self, request, resource_id, *args, **kwargs):
        """
        Handle forms on resource details page.
        """
        post_data = request.POST

        if 'new-workflow' in post_data:
            return self._handle_new_workflow_form(request, resource_id, post_data, *args, **kwargs)

        # Redirect/render the normal GET page by default with warning message.
        messages.warning(request, 'Unable to perform requested action.')
        return self.get(request, resource_id, *args, **kwargs)

    def delete(self, request, resource_id, *args, **kwargs):
        """
        Handle delete requests.
        """
        session = None
        try:
            workflow_id = request.GET.get('id', '')
            log.debug(f'Workflow ID: {workflow_id}')

            make_session = self.get_sessionmaker()
            session = make_session()

            # Get the workflow
            workflow = session.query(ResourceWorkflow).get(workflow_id)

            # Delete the workflow
            session.delete(workflow)
            session.commit()
            log.info(f'Deleted Workflow: {workflow}')
        except:  # noqa: E722
            log.exception('An error occurred while attempting to delete a workflow.')
            return JsonResponse({'success': False, 'error': 'An unexpected error has occurred.'})
        finally:
            session and session.close()

        return JsonResponse({'success': True})

    def _handle_new_workflow_form(self, request, resource_id, params, *args, **kwargs):
        """
        Handle new workflow requests.
        """
        # Params
        workflow_name = params.get('workflow-name', '')
        workflow_type = params.get('workflow-type', '')

        if not workflow_name:
            messages.error(request, 'Unable to create new workflow: no name given.')
            return self.get(request, resource_id, *args, **kwargs)

        if not workflow_type or workflow_type not in self.resource_workflows:
            messages.error(request, 'Unable to create new workflow: invalid workflow type.')
            return self.get(request, resource_id, *args, **kwargs)

        # Create new workflow
        _AppUser = self.get_app_user_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        try:
            WorkflowModel = self.resource_workflows[workflow_type]
            workflow_app = self._app
            workflow = WorkflowModel.new(
                app=workflow_app,
                name=workflow_name,
                resource_id=resource_id,
                creator_id=request_app_user.id,
                geoserver_name=workflow_app.GEOSERVER_NAME,
                map_manager=self.get_map_manager(),
                spatial_manager=self.get_spatial_manager(),
            )
            session.add(workflow)
            session.commit()

        except Exception:
            message = 'An unexpected error occurred while creating the new workflow.'
            log.exception(message)
            messages.error(request, message)
            return self.get(request, resource_id, *args, **kwargs)
        finally:
            session.close()

        messages.success(request, 'Successfully created new {}: {}'.format(
            self.resource_workflows[workflow_type].DISPLAY_TYPE_SINGULAR, workflow_name)
        )
        return self.get(request, resource_id, *args, **kwargs)
