"""
********************************************************************************
* Name: manage_organizations
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Python core
import json
from shutil import rmtree
# Django
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
# Tethys core
from tethys_sdk.base import TethysController
from tethys_sdk.gizmos import ToggleSwitch
from tethys_sdk.permissions import has_permission, permission_required
# ATCore
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
# App User Services
# TODO: Bring these helpers over into organization/services/methods
from tethysapp.epanet.lib.storage_helpers import calculate_storage_stats_for_organization, DEFAULT_STORAGE
from tethysapp.epanet.lib.helpers import get_organization_workspace_path
from tethysext.atcore.services._app_users import remove_all_epanet_permissions_groups, get_user_peers, \
                                                 get_all_permissions_groups_for_user


class ManageOrganizations(TethysController):
    """
    Controller for manage_organizations page.

    GET: Render list of all organizations.
    DELETE: Delete and organization.
    """

    page_title = 'Organizations'
    template_name = 'atcore/app_users/manage_organizations.html'
    http_method_names = ['get', 'delete']

    def get_app_user_model(self):
        return AppUser

    def get_organization_model(self):
        return Organization

    def get_resource_model(self):
        return Resource

    def get_sessionmaker(self):
        return NotImplementedError

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

    # @method_decorator(active_user_required) #TODO: Generalize active_user_required
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

        organizations = sorted(organizations, key=lambda c: c.name)

        # Permissions
        can_modify_organizations = has_permission(request, 'modify_organizations')
        can_modify_organization_members = has_permission(request, 'modify_organization_members')
        can_assign_addon_permissions = has_permission(request, 'assign_addon_permissions')
        can_modify_enterprise_organizations = has_permission(request, 'modify_enterprise_organizations')

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

            # Group clients by type
            clients = {}
            for client in organization.clients:
                if client.DISPLAY_TYPE_PLURAL not in clients:
                    clients[client.DISPLAY_TYPE_PLURAL] = []

                clients[client.DISPLAY_TYPE_PLURAL].append(client.__dict__)

            # Group resources by type
            resources = {}
            for resource in organization.resources:
                if resource.DISPLAY_TYPE_PLURAL not in resources:
                    resources[resource.DISPLAY_TYPE_PLURAL] = []

                resources[resource.DISPLAY_TYPE_PLURAL].append(resource.__dict__)

            # Get permissions
            can_modify = has_permission(request, organization.get_modify_permission())
            can_modify_members = has_permission(request, organization.get_modify_members_permission())

            organization_card = {
                'id': organization.id,
                'name': organization.name,
                'is_active': 'Active' if organization.active else 'Disabled',
                'members': members,
                'clients': clients,
                'consultant': organization.consultant,
                'resources': resources,
                'can_modify': can_modify,
                'can_modify_members': can_modify_members
            }
            from pprint import pprint
            pprint(organization_card)

            # Hook to allow for adding custom fields
            organization_card = self.add_custom_fields(organization, organization_card)

            # Group organizations by display type
            if organization.DISPLAY_TYPE_PLURAL not in organization_cards:
                organization_cards[organization.DISPLAY_TYPE_PLURAL] = []

            organization_cards[organization.DISPLAY_TYPE_PLURAL].append(organization_card)

            # if organization.type == ENTERPRISE_ORG_TYPE:
            #     # initialize client arrays
            #     organization_card['standard_clients'] = []
            #     organization_card['professional_clients'] = []
            #
            #     # Add clients for enterprise orgs
            #     for client in organization.clients:
            #         if client.access_level == ACCESS_STANDARD:
            #             organization_card['standard_clients'].append(client)
            #         elif client.access_level == ACCESS_PROFESSIONAL:
            #             organization_card['professional_clients'].append(client)
            #
            #     enterprise_org_cards.append(organization_card)
            #
            #     # Compute stats for client usage visualization
            #     max_standard = float(organization.get_max_clients_at_level(ACCESS_STANDARD))
            #     used_standard = len(organization_card['standard_clients'])
            #     over_standard = used_standard > max_standard
            #
            #     if over_standard:
            #         percent_standard = 100
            #     else:
            #         if max_standard > 0:
            #             percent_standard = used_standard / max_standard * 100
            #         else:
            #             percent_standard = 0
            #
            #     organization_card['standard_client_stats'] = {
            #         'max': int(max_standard),
            #         'used': int(used_standard),
            #         'percentage': '{0:.0f}'.format(percent_standard) if percent_standard <= 100 else 100,
            #         'over': over_standard
            #     }
            #
            #     max_professional = float(organization.get_max_clients_at_level(ACCESS_PROFESSIONAL))
            #     used_professional = len(organization_card['professional_clients'])
            #     over_professional = used_professional > max_professional
            #
            #     if over_professional:
            #         percent_professional = 100
            #     else:
            #         if max_professional > 0:
            #             percent_professional = used_professional / max_professional * 100
            #         else:
            #             percent_professional = 0
            #
            #     organization_card['professional_client_stats'] = {
            #         'max': int(max_professional),
            #         'used': int(used_professional),
            #         'percentage': '{0:.0f}'.format(percent_professional) if percent_professional <= 100 else 100,
            #         'over': over_professional
            #     }
            #
            #     organization_card['modify_storage'] = has_permission(request, 'manage_enterprise_storage')
            #
            # elif organization.type == CLIENT_ORG_TYPE:
            #     # Add owners for client orgs
            #     organization_card['owners'] = organization.owners
            #     organization_card['modify_storage'] = has_permission(request, 'manage_client_storage')
            #     client_org_cards.append(organization_card)

        session.close()

        context = {
            'page_title': self.page_title,
            'organization_cards': organization_cards,
            'show_new_button': can_modify_organizations,
            'load_delete_modal': can_modify_organizations,
            'show_manage_users_link': has_permission(request, 'view_users'),
            'show_manage_organizations_link': has_permission(request, 'view_organizations'),
            'link_to_members': can_modify_organizations,
            # 'expand_enterprise': len(enterprise_org_cards) <= 1,
            # 'expand_all': len(enterprise_org_cards) + len(client_org_cards) <= 2,
            'show_modify_members_button': can_modify_organization_members,
            'show_edit_enterprise_button': can_modify_organizations,
            'show_edit_and_delete_client_buttons': can_modify_organizations,
            'show_modify_addons_switches': can_assign_addon_permissions
        }

        return render(request, self.template_name, context)

    @permission_required('modify_users')
    def _handle_delete(self, request, organization_id):
        """
        Handle delete user requests.
        """
        _Organization = self.get_organization_model()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()
        try:
            organization = session.query(_Organization).get(organization_id)
            self.perform_custom_delete_operations(request, organization)
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
        return organization_card

    def perform_custom_delete_operations(self, request, organization):
        """
        Hook to perform custom delete operations prior to the organization being deleted.
        Args:
            request(django.Request): the DELETE request object. 
            organization(Organization): the sqlalchemy Organization instance to be deleted. 

        Raises:
            Exception: raise an appropriate exception if an error occurs. The message will be sent as the 'error' field of the JsonResponse.
        """  # noqa: F401
        pass
        # TODO: Implement this in CityWater when migrating to ATCore.
        # org_workspace_path = get_organization_workspace_path(organization.id)
        # rmtree(org_workspace_path)
