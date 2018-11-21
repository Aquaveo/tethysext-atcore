"""
********************************************************************************
* Name: resource_status.py
* Author: nswain
* Created On: September 20, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
# Tethys core
from tethys_sdk.gizmos import JobsTable
from tethys_sdk.permissions import permission_required
from tethys_apps.utilities import get_active_app
# ATCore
from tethysext.atcore.controllers.app_users.base import AppUsersResourceController
from tethysext.atcore.services.app_users.decorators import active_user_required


class ResourceStatus(AppUsersResourceController):
    """
    Controller for resource_status page.

    GET: Render status view of given resource.
    """
    template_name = 'atcore/app_users/resource_status.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get']
    show_detailed_status = True

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request, *args, **kwargs)

    @active_user_required()
    @permission_required('view_resources')
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        # GET PARAMS
        params = request.GET
        resource_id = params.get('r', None)

        resource = None
        app = self.get_app()
        job_manager = app.get_job_manager()
        jobs = job_manager.list_jobs()

        # Filter by resource
        filtered_jobs = []

        if resource_id:
            # This checks for existence of the resource and access permissions
            resource = self.get_resource(request, resource_id)

            # TODO: Move permissions check into decorator
            if isinstance(resource, HttpResponse):
                return resource

            for job in jobs:
                # Cannot associate job resource id if no resource_id provided in extended properties
                if 'resource_id' not in job.extended_properties:
                    continue

                # Skip jobs that are not associated with this resource.
                if job.extended_properties['resource_id'] != resource_id:
                    continue

                filtered_jobs.append(job)
        else:
            # TODO: Should this be filtered down more? By user? Permissions?
            filtered_jobs = jobs

        jobs_table = JobsTable(
            jobs=filtered_jobs,
            column_fields=('id', 'name', 'creation_time', 'execute_time', 'run_time'),
            hover=True,
            striped=False,
            bordered=False,
            condensed=False,
            show_detailed_status=self.show_detailed_status
        )

        context = {
            'jobs_table': jobs_table,
            'resource_id': resource_id,
            'resource': resource,
            'base_template': self.base_template,
            'back_url': self.back_url
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
        resource_id = kwargs.get('resource_id', None)
        back_arg = request.GET.get('back', '')
        active_app = get_active_app(request)
        app_namespace = active_app.namespace
        if back_arg == 'resource-details' and resource_id:
            back_controller = reverse('{}:app_users_resource_details'.format(app_namespace), args=[resource_id])
        else:
            back_controller = reverse('{}:app_users_manage_resources'.format(app_namespace))
        return back_controller

    def get_context(self, request, context):
        """
        Hook for modifying context.

        Args:
            request(HttpRequest): Django HttpRequest.
            context(dict): context object.

        Returns:
            dict: context
        """
        return context
