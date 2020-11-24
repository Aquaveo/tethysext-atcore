"""
********************************************************************************
* Name: manage_resources.py
* Author: nswain
* Created On: April 18, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import logging
# Django
from django.http import JsonResponse
from django.shortcuts import render, reverse

# Tethys core
from tethys_sdk.permissions import has_permission, permission_required
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.services.paginate import paginate


log = logging.getLogger(__name__)


class ManageResources(AppUsersViewMixin):
    """
    Controller for manage_resources page.

    GET: Render list of all resources.
    DELETE: Delete and organization.
    """
    template_name = 'atcore/app_users/manage_resources.html'
    base_template = 'atcore/app_users/base.html'
    default_action_title = 'Launch'
    http_method_names = ['get', 'delete']

    ACTION_LAUNCH = 'launch'
    ACTION_PROCESSING = 'processing'
    ACTION_ERROR = 'error'

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request)

    def delete(self, request, *args, **kwargs):
        """
        Route delete requests.
        """
        action = request.GET.get('action', None)
        user_id = request.GET.get('id', None)

        if action == 'delete':
            return self._handle_delete(request, user_id)

        return JsonResponse({'success': False, 'error': 'Invalid action: {}'.format(action)})

    @active_user_required()
    @permission_required('view_resources', 'view_all_resources', use_or=True)
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        # User setting constants
        _SETTINGS_PAGE = 'projects'
        _SETTING_PROJECTS_PER_PAGE = 'setting_projects-per-page'
        _SETTING_SORT_PROJECT_BY = 'setting_sort-projects-by'

        # Setup
        _AppUser = self.get_app_user_model()

        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # GET params
        params = request.GET

        page = int(params.get('page', 1))
        results_per_page = params.get('show', None)
        sort_by_raw = params.get('sort_by', None)

        # Update setting if user made a change
        if results_per_page:
            request_app_user.update_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_PROJECTS_PER_PAGE,
                value=results_per_page
            )

        # Get the existing user setting if loading for the first time
        else:
            results_per_page = request_app_user.get_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_PROJECTS_PER_PAGE,
                as_value=True
            )

        # Update setting if user made a change
        if sort_by_raw:
            request_app_user.update_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_SORT_PROJECT_BY,
                value=sort_by_raw
            )

        # Get the existing user setting if loading for the first time
        else:
            sort_by_raw = request_app_user.get_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_SORT_PROJECT_BY,
                as_value=True
            )

        # Set default settings if not set
        if not results_per_page:
            results_per_page = 10
        if not sort_by_raw:
            sort_by_raw = 'date_created:reverse'

        results_per_page = int(results_per_page)

        sort_reversed = ':reverse' in sort_by_raw
        sort_by = sort_by_raw.split(':')[0]

        # Get the resources
        all_resources = self.get_resources(session, request, request_app_user)

        # Build cards
        resource_cards = []
        for resource in all_resources:
            resource_card = resource.__dict__
            resource_card['editable'] = self.can_edit_resource(session, request, resource)
            resource_card['deletable'] = self.can_delete_resource(session, request, resource)
            resource_card['organizations'] = resource.organizations
            resource_card['debugging'] = resource.attributes
            resource_card['debugging']['id'] = str(resource.id)

            # Get resource action parameters
            action_dict = self.get_resource_action(
                session=session,
                request=request,
                request_app_user=request_app_user,
                resource=resource
            )

            resource_card['action'] = action_dict['action']
            resource_card['action_title'] = action_dict['title']
            resource_card['action_href'] = action_dict['href']

            resource_cards.append(resource_card)

        # Only attempt to sort if the sort field is a valid attribute of _Resource
        if hasattr(_Resource, sort_by):
            sorted_resources = sorted(
                resource_cards,
                key=lambda resource_card: (not resource_card[sort_by], resource_card[sort_by]),
                reverse=sort_reversed
            )
        else:
            sorted_resources = resource_cards

        # Generate pagination
        paginated_resources, pagination_info = paginate(
            objects=sorted_resources,
            results_per_page=results_per_page,
            page=page,
            result_name='projects',
            sort_by_raw=sort_by_raw,
            sort_reversed=sort_reversed
        )
        context = self.get_base_context(request)
        context.update({
            'page_title': _Resource.DISPLAY_TYPE_PLURAL,
            'type_plural': _Resource.DISPLAY_TYPE_PLURAL,
            'type_singular': _Resource.DISPLAY_TYPE_SINGULAR,
            'resource_slug': _Resource.SLUG,
            'base_template': self.base_template,
            'resources': paginated_resources,
            'pagination_info': pagination_info,
            'show_new_button': has_permission(request, 'create_resource'),
            'show_debugging_info': request_app_user.is_staff(),
            'load_delete_modal': has_permission(request, 'delete_resource'),
            'show_links_to_organizations': has_permission(request, 'edit_organizations'),
            'show_users_link': has_permission(request, 'modify_users'),
            'show_resources_link': has_permission(request, 'view_resources'),
            'show_organizations_link': has_permission(request, 'view_organizations')
        })

        session.close()

        return render(request, self.template_name, context)

    @permission_required('delete_resource')
    def _handle_delete(self, request, resource_id):
        """
        Handle delete user requests.
        """
        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()

        try:
            resource = session.query(_Resource).get(resource_id)
            try:
                self.perform_custom_delete_operations(request, resource)
            except:  # noqa: E722
                log.warning(f'Unable to perform custom delete operations on resource {resource}.')
            session.delete(resource)
            session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}

        session.close()
        return JsonResponse(json_response)

    def get_resource_action(self, session, request, request_app_user, resource):
        """
        Get the parameters that define the action button (i.e.: Launch button).

        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.

        Returns:
            dict<action, title, href>: action attributes.
        """
        status = resource.get_status(resource.ROOT_STATUS_KEY, resource.STATUS_EMPTY)

        if status in resource.ERROR_STATUSES:
            return {
                'action': self.ACTION_ERROR,
                'title': 'Error',
                'href': reverse(f'{self._app.namespace}:{resource.SLUG}_resource_details', args=[resource.id])
            }

        elif status in resource.WORKING_STATUSES:
            processing_url = reverse(f'{self._app.namespace}:{resource.SLUG}_resource_status')
            return {
                'action': self.ACTION_PROCESSING,
                'title': 'Processing',
                'href': processing_url + '?r={}'.format(resource.id)
            }

        else:
            return {
                'action': self.ACTION_LAUNCH,
                'title': self.default_action_title,
                'href': reverse(f'{self._app.namespace}:{resource.SLUG}_resource_details', args=[resource.id])
            }

    def get_resources(self, session, request, request_app_user):
        """
        Hook to allow easy customization of the resources query.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
        Returns:
            list<Resources>: the list of resources to render on the manage_resources page.
        """
        return request_app_user.get_resources(session, request)

    def perform_custom_delete_operations(self, request, resource):
        """
        Hook to perform custom delete operations prior to the resource being deleted.
        Args:
            request(django.Request): the DELETE request object.
            resource(Resource): the sqlalchemy Resource instance to be deleted.

        Raises:
            Exception: raise an appropriate exception if an error occurs. The message will be sent as the 'error' field of the JsonResponse.
        """  # noqa: E501
        pass

    def can_edit_resource(self, session, request, resource):
        """
        Hook into resource_card.editable attribute to allow for more than permissions-based check.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.Request): the request object.
            resource(Resource): current resource.

        Returns:
            bool: the edit button will be displayed for this resource if True.
        """
        return has_permission(request, 'edit_resource')

    def can_delete_resource(self, session, request, resource):
        """
        Hook into resource_card.deletable attribute to allow for more than permissions-based check.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.Request): the request object.
            resource(Resource): current resource.

        Returns:
            bool: the delete button will be displayed for this resource if True.
        """
        return has_permission(request, 'delete_resource') or has_permission(request, 'always_delete_resource')
