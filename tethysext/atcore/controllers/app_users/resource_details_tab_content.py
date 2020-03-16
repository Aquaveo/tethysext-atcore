"""
********************************************************************************
* Name: resource_details_tab_content.py
* Author: nswain, glarsen
* Created On: August 09, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from django.shortcuts import render, reverse
from django.http import HttpResponseNotFound, HttpResponse
from tethys_sdk.permissions import permission_required, has_permission
from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.controllers.app_users import ResourceDetails
from tethysext.atcore.controllers.utiltities import get_style_for_status
from tethysext.atcore.models.app_users.app_user import AppUser
from tethysext.atcore.services.app_users.roles import Roles

log = logging.getLogger(__name__)


class ResourceDetailsTabContent(ResourceDetails):
    """
    Controller for resource_details page.

    GET: Render detail view of given resource.
    """
    template_name = None
    base_template = 'atcore/base.html'
    http_method_names = ['get']
    show_all_workflows = True
    show_all_workflows_roles = [Roles.APP_ADMIN, Roles.DEVELOPER, Roles.ORG_ADMIN, Roles.ORG_REVIEWER]

    def preview_image(self, *args, **kwargs):
        """
        Preview image for summary tab

        Override this to get an image back, return a a tuple of (Image Title, URL)
        """
        return None

    def get_summary_tab_info(self, request, resource):
        """
        Get the summary tab info

        Return Format
        [
            [
                ('Section 1 Title', {'key1': value}),
                ('Section 2 Title', {'key1': value, 'key2': value}),
            ],
            [
                ('Section 3 Title', {'key1': value}),
            ],
        ]
        """
        return []

    @active_user_required()
    @permission_required('view_resources')
    def _handle_get(self, request, resource_id, tab, *args, **kwargs):
        """
        Handle get requests.
        """
        # Verifies permissions on resource
        resource = self.get_resource(request, resource_id)

        if isinstance(resource, HttpResponse):
            return resource

        context = {
            'resource': resource,
            'back_url': self.back_url
        }

        tab_handler_map = {
            'summary': self._handle_summary_tab,
            'workflows': self._handle_workflows_tab
        }

        resource_preview_image = self.preview_image(request, context)
        if resource_preview_image is not None:
            tab_handler_map.update({
                'summary-preview-image': self._handle_summary_tab_preview_image
            })

        try:
            response = tab_handler_map[tab](request, resource_id, context, *args, **kwargs)
        except KeyError:
            response = HttpResponseNotFound('"{}" is not a valid tab.'.format(tab))

        return response

    def _handle_summary_tab(self, request, resource_id, context, *args, **kwargs):
        """
        Render the summary tab content.

        Returns:
            HttpResponse: rendered template.
        """
        resource = context['resource']
        preview_image = self.preview_image(request, context)
        has_preview_image = preview_image is not None
        context['has_preview_image'] = has_preview_image
        if has_preview_image:
            context['preview_image_title'] = preview_image[0]

        general_summary_tab_info = ('Description', {'Name': resource.name, 'Description': resource.description,
                                    'Created By': resource.created_by, 'Date Created': resource.date_created})

        # Add general_summary_tab_info as first item in first columns
        summary_tab_info = self.get_summary_tab_info(request, resource)
        if len(summary_tab_info) == 0:
            summary_tab_info = [[general_summary_tab_info]]
        else:
            summary_tab_info[0].insert(0, general_summary_tab_info)

        # Debug Section
        if request.user.is_staff:
            debug_atts = {x.replace("_", " ").title(): y for x, y in resource.attributes.items() if x != 'files'}
            debug_atts['Locked'] = resource.is_user_locked

            if resource.is_user_locked:
                debug_atts['Locked By'] = 'All Users' if resource.is_locked_for_all_users else resource.user_lock
            else:
                debug_atts['Locked By'] = 'N/A'

            debug_summary_tab_info = ('Debug Info', debug_atts)
            summary_tab_info[-1].append(debug_summary_tab_info)

        context['columns'] = summary_tab_info

        return render(request, 'atcore/app_users/resource_details/summary.html', context)

    def _handle_summary_tab_preview_image(self, request, resource_id, context, *args, **kwargs):
        """
        Render the summary tab preview image.

        Returns:
            HttpResponse: rendered template.
        """
        context['preview_title'], context['preview_map_url'] = self.preview_image(request, context)
        return render(request, 'atcore/app_users/resource_details/summary_preview_image.html', context)

    def _handle_workflows_tab(self, request, resource_id, context, *args, **kwargs):
        """
        Render the workflows tab content.

        Returns:
            HttpResponse: rendered template.
        """

        make_session = self.get_sessionmaker()
        session = make_session()

        try:
            breakpoint()
            app_user_name = request.user.username
            app_user = session.query(AppUser).filter(AppUser.username == app_user_name).one()
            app_user_role = app_user.role
            if self.show_all_workflows or app_user_role in self.show_all_workflows_roles:
                workflows = session.query(ResourceWorkflow).\
                    filter(ResourceWorkflow.resource_id == resource_id).\
                    order_by(ResourceWorkflow.date_created.desc()).\
                    all()
            else:
                workflows = session.query(ResourceWorkflow). \
                    filter(ResourceWorkflow.resource_id == resource_id). \
                    filter(ResourceWorkflow.creator_id == app_user.id). \
                    order_by(ResourceWorkflow.date_created.desc()). \
                    all()

            # Build up workflow cards for workflows table
            workflow_cards = []

            for workflow in workflows:
                status = workflow.get_status()
                app_namespace = self.get_app().namespace
                url_name = f'{app_namespace}:{workflow.TYPE}_workflow'
                href = reverse(url_name, args=(resource_id, str(workflow.id)))

                status_style = get_style_for_status(status)

                if status == workflow.STATUS_PENDING or status == '' or status is None:
                    statusdict = {
                        'title': 'Begin',
                        'style': 'primary',
                        'href': href
                    }

                elif status == workflow.STATUS_WORKING:
                    statusdict = {
                        'title': 'Running',
                        'style': status_style,
                        'href': href
                    }

                elif status == workflow.STATUS_COMPLETE:
                    statusdict = {
                        'title': 'View Results',
                        'style': status_style,
                        'href': href
                    }

                elif status == workflow.STATUS_ERROR:
                    statusdict = {
                        'title': 'Continue',
                        'style': 'primary',
                        'href': href
                    }

                elif status == workflow.STATUS_FAILED:
                    statusdict = {
                        'title': 'Failed',
                        'style': status_style,
                        'href': href  # TODO: MAKE IT POSSIBLE TO RESTART WORKFLOW?
                    }

                else:
                    statusdict = {
                        'title': status,
                        'style': status_style,
                        'href': href
                    }

                is_creator = request.user.username == workflow.creator.username if workflow.creator else True

                workflow_cards.append({
                    'id': str(workflow.id),
                    'name': workflow.name,
                    'type': self.resource_workflows[workflow.type].DISPLAY_TYPE_SINGULAR,
                    'creator': workflow.creator.username if workflow.creator else 'Unknown',
                    'date_created': workflow.date_created,
                    'resource': workflow.resource,
                    'status': statusdict,
                    'can_delete': has_permission(request, 'delete_any_workflow') or is_creator
                })

            context.update({'workflow_cards': workflow_cards})

        finally:
            session.close()

        return render(request, 'atcore/app_users/resource_details/workflows.html', context)
