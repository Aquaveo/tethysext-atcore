"""
********************************************************************************
* Name: resource_status.py
* Author: nswain
* Created On: September 20, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Python
import os
# Django
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
# Tethys core
from tethys_sdk.gizmos import JobsTable
from tethys_sdk.permissions import permission_required
from tethys_apps.utilities import get_active_app
# ATCore
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required, resource_controller


class ResourceStatus(ResourceViewMixin):
    """
    Controller for resource_status page.

    GET: Render status view of given resource.
    """
    template_name = 'atcore/app_users/resource_status.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get']
    show_detailed_status = True
    jobs_table_refresh_interval = int(os.getenv('JOBS_TABLE_REFRESH_INTERVAL', 30000))  # ms

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
        resource_id = None
        if isinstance(resource, HttpResponse):
            return resource
        app = self.get_app()
        job_manager = app.get_job_manager()
        jobs = job_manager.list_jobs()
        app_user = self._AppUser.get_app_user_from_request(request, session)

        # Filter by resource
        filtered_jobs = []

        if resource is not None:
            # This checks for existence of the resource and access permissions
            resource_id = str(resource.id)
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

        # Job logs contain sensitive information, so only show them to staff and app admins
        show_job_table_actions = app_user.is_staff() or app_user.get_role() in [
            self._AppUser.ROLES.APP_ADMIN,
            self._AppUser.ROLES.ORG_ADMIN
        ]
        jobs_table = JobsTable(
            jobs=filtered_jobs,
            column_fields=('id', 'name', 'creation_time', 'execute_time', 'run_time'),
            hover=True,
            striped=False,
            bordered=False,
            condensed=False,
            show_status=True,
            actions=['logs', 'resubmit'],
            show_actions=show_job_table_actions,
            show_detailed_status=self.show_detailed_status,
            refresh_interval=self.jobs_table_refresh_interval,
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
        app_namespace = active_app.url_namespace
        _Resource = self.get_resource_model()
        if back_arg == 'resource-details' and resource_id:
            back_controller = reverse(f'{app_namespace}:{_Resource.SLUG}_resource_details', args=[resource_id])
        else:
            back_controller = reverse(f'{app_namespace}:{_Resource.SLUG}_manage_resources')
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
