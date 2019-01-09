"""
********************************************************************************
* Name: manage_organizations
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render

# Tethys core
from tethys_sdk.permissions import has_permission, permission_required
# ATCore
from tethysext.atcore.controllers.app_users.base import AppUsersController
from tethysext.atcore.services.app_users.decorators import active_user_required


class ManageOrganizations(AppUsersController):
    """
    Controller for manage_organizations page.

    GET: Render list of all organizations.
    DELETE: Delete and organization.
    """
    template_name = 'atcore/app_users/manage_organizations.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get', 'delete']

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
    @permission_required('view_organizations')
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # List organizations: admins can see all, everyone else can see only the organizations to which they belong
        if request_app_user.is_staff() or has_permission(request, 'view_all_organizations'):
            organizations = session.query(_Organization).all()
        else:
            organizations = request_app_user.get_organizations(session, request, cascade=True)

        organizations = sorted(organizations, key=lambda c: (c.license, c.name))

        # Permissions
        can_create_organizations = has_permission(request, _Organization.get_create_permission())
        can_delete_organizations = has_permission(request, _Organization.get_delete_permission())
        can_modify_users = has_permission(request, 'modify_users')
        load_delete_modal = can_delete_organizations

        # Create cards for organizations
        organization_cards = {}

        for organization in organizations:
            members = set()
            for app_user in organization.members:
                members.add(
                    (
                        app_user.get_display_name(append_username=True),
                        str(app_user.id)
                    )
                )

            # Group clients by license
            clients = []
            for client in organization.clients:
                client_dict = client.__dict__
                client_dict['license_display_name'] = _Organization.LICENSES.get_display_name_for(client.license)
                clients.append(client_dict)

            # Group resources by type
            resources = {}
            for resource in organization.resources:
                if resource.DISPLAY_TYPE_PLURAL not in resources:
                    resources[resource.DISPLAY_TYPE_PLURAL] = []

                resources[resource.DISPLAY_TYPE_PLURAL].append(resource.__dict__)

            # Get custom_permissions
            can_edit = has_permission(request, organization.get_edit_permission())
            can_delete = has_permission(request, organization.get_delete_permission()) \
                or organization.consultant is not None
            if can_delete:
                load_delete_modal = True
            can_modify_members = has_permission(request, organization.get_modify_members_permission())

            organization_card = {
                'id': organization.id,
                'name': organization.name,
                'is_active': 'Active' if organization.active else 'Disabled',
                'members': members,
                'clients': clients,
                'consultant': organization.consultant,
                'resources': resources,
                'can_edit': can_edit,
                'can_delete': can_delete,
                'can_modify_members': can_modify_members,
                'license': _Organization.LICENSES.get_display_name_for(organization.license)
            }

            # Hook to allow for adding custom fields
            organization_card = self.add_custom_fields(organization, organization_card)

            # Group organizations by display type
            license_display = _Organization.LICENSES.get_display_name_for(organization.license)
            if license_display not in organization_cards:
                organization_cards[license_display] = []

            organization_cards[license_display].append(organization_card)

        session.close()

        context = {
            'page_title': _Organization.DISPLAY_TYPE_PLURAL,
            'base_template': self.base_template,
            'organization_cards': organization_cards,
            'show_new_button': can_create_organizations,
            'load_delete_modal': load_delete_modal,
            'link_to_members': can_modify_users,
            'show_users_link': can_modify_users,
            'show_resources_link': has_permission(request, 'view_resources'),
            'show_organizations_link': has_permission(request, 'view_organizations')
        }

        return render(request, self.template_name, context)

    def _handle_delete(self, request, organization_id):
        """
        Handle delete user requests.
        """
        _Organization = self.get_organization_model()
        _AppUser = self.get_app_user_model()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()

        try:
            request_app_user = _AppUser.get_app_user_from_request(request, session)
            organization = session.query(_Organization).get(organization_id)
            self.perform_custom_delete_operations(request, organization)

            # Validate permission to delete the organization
            can_delete_organizations = has_permission(request, 'delete_organizations')

            # If user is a member of the consultant organization and admin they can delete it
            consultant = organization.consultant

            if consultant is not None and consultant in request_app_user.organizations \
               and request_app_user.role == _AppUser.ROLES.ORG_ADMIN:
                can_delete_organizations = True

            if not can_delete_organizations:
                return HttpResponseForbidden()

            session.delete(organization)
            session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}
        session.close()
        return JsonResponse(json_response)

    def add_custom_fields(self, organization, organization_card):
        """
        Hook to add custom fields to each organization card.
        Args:
            organization(Organization): the sqlalchemy Organization instance.
            organization_card(dict): the default organization card.
        Returns:
            dict: customized organization card.
        """
        # TODO ask nathan what the purpose of this function is.
        return organization_card

    def perform_custom_delete_operations(self, request, organization):
        """
        Hook to perform custom delete operations prior to the organization being deleted.
        Args:
            request(django.Request): the DELETE request object.
            organization(Organization): the sqlalchemy Organization instance to be deleted.

        Raises:
            Exception: raise an appropriate exception if an error occurs. The message will be sent as the 'error' field of the JsonResponse.
        """  # noqa: E501
        pass
        # TODO: Implement this in CityWater when migrating to ATCore.
        # org_workspace_path = get_organization_workspace_path(organization.id)
        # rmtree(org_workspace_path)
