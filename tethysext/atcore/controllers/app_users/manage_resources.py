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
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.services.paginate import paginate


log = logging.getLogger(f'tethys.{__name__}')


class ManageResources(ResourceViewMixin):
    """
    Controller for manage_resources page.

    GET: Render list of all resources.
    DELETE: Delete and organization.
    """
    template_name = 'atcore/app_users/manage_resources.html'
    base_template = 'atcore/app_users/base.html'
    row_template = 'atcore/components/resource_row.html'
    default_action_title = 'Launch'
    default_action_icon = "bi-chevron-right"
    error_action_title = "Error"
    error_action_icon = "bi-x-lg"
    working_action_title = "Processing"
    working_action_icon = "bi-arrow-clockwise"
    http_method_names = ['get', 'post', 'delete']
    enable_groups = False
    collapse_groups = False
    highlight_groups = False
    show_archive_button = False
    # Opt-in: set True in a subclass to render the list as a client-side jQuery DataTable
    # (search box, sortable headers, page-size selector). Ignored when enable_groups is True.
    enable_datatable = False

    ACTION_LAUNCH = 'launch'
    ACTION_PROCESSING = 'processing'
    ACTION_ERROR = 'error'

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        action = request.POST.get('action', None)

        if action == 'new-group-from-selected':
            return self._handle_new_group_from_selected(request)

        return JsonResponse({'success': False, 'error': 'Invalid action: {}'.format(action)})

    def delete(self, request, *args, **kwargs):
        """
        Route delete requests.
        """
        action = request.GET.get('action', None)
        user_id = request.GET.get('id', None)

        if action == 'delete':
            return self._handle_delete(request, user_id)

        if action == 'archive':
            return self._handle_archive(request, user_id)

        return JsonResponse({'success': False, 'error': 'Invalid action: {}'.format(action)})

    @active_user_required()
    @permission_required('view_resources', 'view_all_resources', use_or=True)
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        # User setting constants
        _SETTINGS_PAGE = 'resources'
        _SETTING_RESOURCES_PER_PAGE = 'setting_resources-per-page'
        _SETTING_SORT_RESOURCE_BY = 'setting_sort-resources-by'

        # Setup
        _AppUser = self.get_app_user_model()

        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # GET params
        params = request.GET

        page = int(params.get('page', 1))
        resources_per_page = params.get('show', None)
        sort_by_raw = params.get('sort_by', None)
        # Transient (not persisted as a user setting) server-side search term. Only used on the
        # non-DataTable path; the DataTable filters client-side and never sends this param.
        search = (params.get('search', '') or '').strip()

        # Update setting if user made a change
        if resources_per_page:
            request_app_user.update_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_RESOURCES_PER_PAGE,
                value=resources_per_page
            )

        # Get the existing user setting if loading for the first time
        else:
            resources_per_page = request_app_user.get_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_RESOURCES_PER_PAGE,
                as_value=True
            )

        # Update setting if user made a change
        if sort_by_raw:
            request_app_user.update_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_SORT_RESOURCE_BY,
                value=sort_by_raw
            )

        # Get the existing user setting if loading for the first time
        else:
            sort_by_raw = request_app_user.get_setting(
                session=session,
                page=_SETTINGS_PAGE,
                key=_SETTING_SORT_RESOURCE_BY,
                as_value=True
            )

        # Set default settings if not set
        if not resources_per_page:
            resources_per_page = 10
        if not sort_by_raw:
            sort_by_raw = 'date_created:reverse'

        resources_per_page = int(resources_per_page)

        sort_reversed = ':reverse' in sort_by_raw
        sort_by = sort_by_raw.split(':')[0]

        # Get the resources
        all_resources = self.get_resources(session, request, request_app_user)

        # Build cards
        def build_resource_cards(resources, level=0):
            resource_cards = []
            for resource in resources:
                # Skip resources that have "hidden" statuses
                if resource.get_status(resource.ROOT_STATUS_KEY) in resource.HIDDEN_STATUSES:
                    continue

                resource_card = resource.__dict__ if getattr(resource, '__dict__', None) else dict()
                resource_card['level'] = level
                resource_card['slug'] = resource.SLUG
                resource_card['editable'] = self.can_edit_resource(session, request, resource)
                resource_card['deletable'] = self.can_delete_resource(session, request, resource)
                resource_card['archivable'] = self.show_archive_button and self.can_archive_resource(
                    session, request, resource
                )
                resource_card['organizations'] = resource.organizations
                resource_card['attributes'] = resource.attributes
                resource_card['attributes']['id'] = str(resource.id)
                resource_card['has_parents'] = len(resource.parents) > 0
                resource_card['has_children'] = len(resource.children) > 0

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
                resource_card['action_icon'] = action_dict['icon']
                resource_card['info_href'] = self.get_info_url(request, resource)

                # Build child resources recursively
                resource_card['children'] = build_resource_cards(resource.children, level=level+1) \
                    if self.enable_groups and resource.children else []

                # append resource to resource_cards
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
            return sorted_resources

        resource_cards = build_resource_cards(all_resources)

        # DataTables handles search/sort/paging client-side, so it needs all rows rendered.
        # Server-side pagination is only used for the grouped (hierarchical) view.
        use_datatable = self.enable_datatable and not self.enable_groups

        # Apply the server-side search filter when the search feature is enabled but the
        # client-side DataTable is not in use (i.e. the grouped view). The filter is
        # hierarchy-aware so parent/child relationships in the grouped view are preserved.
        if search and self.enable_datatable and not use_datatable:
            resource_cards = self.filter_resource_cards(resource_cards, search.lower())

        # Generate pagination
        paginated_resources, pagination_info = paginate(
            objects=resource_cards,
            results_per_page=resources_per_page,
            page=page,
            result_name=_Resource.DISPLAY_TYPE_PLURAL,
            sort_by_raw=sort_by_raw,
            sort_reversed=sort_reversed
        )

        # The DataTable paginates in the browser, so render every card rather than a single
        # server-side page. The user's settings still drive the initial state via pagination_info.
        if use_datatable:
            paginated_resources = resource_cards

        # Make the active search term available to the pagination links and the search input.
        # Empty on the DataTable path.
        pagination_info['search'] = search

        context = self.get_base_context(request)
        context.update({
            'enable_datatable': self.enable_datatable,
            'use_datatable': use_datatable,
            'search': search,
            'collapse_groups': self.collapse_groups,
            'highlight_groups': self.highlight_groups,
            'page_title': _Resource.DISPLAY_TYPE_PLURAL,
            'type_plural': _Resource.DISPLAY_TYPE_PLURAL,
            'type_singular': _Resource.DISPLAY_TYPE_SINGULAR,
            'resource_slug': _Resource.SLUG,
            'base_template': self.base_template,
            'row_template': self.row_template,
            'resources': paginated_resources,
            'pagination_info': pagination_info,
            'show_select_column': self.enable_groups and has_permission(request, 'create_resource'),
            'show_group_buttons': self.enable_groups,
            'enable_groups': self.enable_groups,
            'show_new_group_button': self.enable_groups and has_permission(request, 'create_resource'),
            'show_new_button': has_permission(request, 'create_resource'),
            'show_attributes': request_app_user.is_staff(),
            'load_delete_modal': has_permission(request, 'delete_resource'),
            'load_archive_modal': self.show_archive_button and has_permission(request, 'delete_resource'),
            'show_links_to_organizations': has_permission(request, 'edit_organizations'),
            'show_users_link': has_permission(request, 'modify_users'),
            'show_resources_link': has_permission(request, 'view_resources'),
            'show_organizations_link': has_permission(request, 'view_organizations'),
            'show_organizations_column': len(request_app_user.get_organizations(session, request)) > 1,
        })

        session.close()

        return render(request, self.template_name, context)

    @active_user_required()
    @permission_required('create_resource')
    def _handle_new_group_from_selected(self, request):
        """
        Handle creating new "group" resource (resource with children).
        """
        _AppUser = self.get_app_user_model()
        _Resource = self.get_resource_model()
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        children = request.POST.getlist('children', [])
        json_response = {'success': True}

        if not name:
            json_response['success'] = False
            json_response['error'] = 'Name is required.'
            return JsonResponse(json_response)

        log.debug(f'Creating new {_Resource.DISPLAY_TYPE_SINGULAR} group named "{name}" with children {children}')

        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        try:
            # Create new resource
            resource = _Resource()
            resource.name = name
            resource.description = description
            resource.created_by = request_app_user.username
            session.add(resource)
            session.commit()

            # Get child resources
            for child_id in children:
                child_resource = session.query(_Resource).get(child_id)
                resource.children.append(child_resource)

                for organization in child_resource.organizations:
                    if organization not in resource.organizations:
                        resource.organizations.append(organization)

            session.commit()

        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}

        session.close()
        return JsonResponse(json_response)

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
                self.perform_custom_delete_operations(session, request, resource)
            except Exception:  # noqa: E722
                log.exception(f'Unable to perform custom delete operations on resource {resource}.')
            session.delete(resource)
            session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}

        session.close()
        return JsonResponse(json_response)

    @permission_required('delete_resource')
    def _handle_archive(self, request, resource_id):
        """
        Handle archive resource requests.
        """
        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()

        try:
            resource = session.query(_Resource).get(resource_id)
            if len(resource.children) > 0:
                json_response = {'success': False,
                                 'error': 'Cannot archive a resource that has child resources.'}
            else:
                try:
                    self.perform_custom_archive_operations(session, request, resource)
                except Exception:  # noqa: E722
                    log.exception(f'Unable to perform custom archive operations on resource {resource}.')
                resource.set_status(resource.ROOT_STATUS_KEY, resource.STATUS_ARCHIVED)
                session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}

        session.close()
        return JsonResponse(json_response)

    def get_working_url(self, request, resource):
        """
        Get the URL for the Resource Working button.
        """
        return reverse(f'{self._app.url_namespace}:{resource.SLUG}_resource_status', args=[resource.id])

    def get_launch_url(self, request, resource):
        """
        Get the URL for the Resource Launch button.
        """
        return reverse(f'{self._app.url_namespace}:{resource.SLUG}_resource_details', args=[resource.id])

    def get_error_url(self, request, resource):
        """
        Get the URL for the Resource Error button.
        """
        return reverse(f'{self._app.url_namespace}:{resource.SLUG}_resource_details', args=[resource.id])

    def get_info_url(self, request, resource):
        """
        Get the URL for the Resource name link and row click.
        """
        # Default to the same as the launch url for backwards compatibility
        return self.get_launch_url(request, resource)

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
                'title': self.error_action_title,
                'href': self.get_error_url(request, resource),
                'icon': self.error_action_icon,
            }

        elif status in resource.WORKING_STATUSES:
            return {
                'action': self.ACTION_PROCESSING,
                'title': self.working_action_title,
                'href': self.get_working_url(request, resource),
                'icon': self.working_action_icon,
            }

        else:
            return {
                'action': self.ACTION_LAUNCH,
                'title': self.default_action_title,
                'href': self.get_launch_url(request, resource),
                'icon': self.default_action_icon,
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
        _Resource = self.get_resource_model()
        return request_app_user.get_resources(
            session, request, of_type=_Resource, include_children=not self.enable_groups
        )

    def filter_resource_cards(self, resource_cards, search_lower, ancestor_match=False):
        """
        Recursively filter resource cards by a (lower-cased) search term, preserving hierarchy.

        A card is kept if it matches, if one of its ancestors matched (in which case the whole
        subtree is kept), or if one of its descendants matched (so the ancestor chain leading to a
        match is retained). Non-matching branches are pruned.

        Args:
            resource_cards(list<dict>): resource cards to filter (each may contain a 'children' list).
            search_lower(str): the search term, already lower-cased.
            ancestor_match(bool): True if an ancestor of these cards already matched the term.

        Returns:
            list<dict>: the filtered (and pruned) list of resource cards.
        """
        filtered = []
        for resource_card in resource_cards:
            self_match = ancestor_match or self.resource_card_matches_search(resource_card, search_lower)
            children = self.filter_resource_cards(
                resource_card.get('children') or [], search_lower, self_match
            )
            if self_match or children:
                resource_card['children'] = children
                filtered.append(resource_card)
        return filtered

    def resource_card_matches_search(self, resource_card, search_lower):
        """
        Hook to determine whether a single resource card matches the search term.

        Override to change which fields are searched. The term is a case-insensitive substring.

        Args:
            resource_card(dict): the resource card to test.
            search_lower(str): the search term, already lower-cased.

        Returns:
            bool: True if the card matches the search term.
        """
        return (
            search_lower in (resource_card.get('name') or '').lower()
            or search_lower in (resource_card.get('description') or '').lower()
            or search_lower in (resource_card.get('created_by') or '').lower()
        )

    def perform_custom_delete_operations(self, session, request, resource):
        """
        Hook to perform custom delete operations prior to the resource being deleted.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.Request): the DELETE request object.
            resource(Resource): the sqlalchemy Resource instance to be deleted.

        Raises:
            Exception: raise an appropriate exception if an error occurs. The message will be sent as the 'error' field of the JsonResponse.
        """  # noqa: E501
        pass

    def perform_custom_archive_operations(self, session, request, resource):
        """
        Hook to perform custom operations prior to the resource being archived.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.Request): the DELETE request object.
            resource(Resource): the sqlalchemy Resource instance to be archived.

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

    def can_archive_resource(self, session, request, resource):
        """
        Hook into resource_card.archivable attribute to allow for more than permissions-based check.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.Request): the request object.
            resource(Resource): current resource.

        Returns:
            bool: the archive button will be displayed for this resource if True.
        """
        can_delete = has_permission(request, 'delete_resource') or has_permission(request, 'always_delete_resource')
        return can_delete and len(resource.children) == 0
