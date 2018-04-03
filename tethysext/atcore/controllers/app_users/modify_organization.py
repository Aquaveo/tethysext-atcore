"""
********************************************************************************
* Name: modify_organization
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Python core
import json
# Django
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
# Tethys core
from tethys_apps.base.controller import TethysController
from tethys_apps.decorators import permission_required
from tethys_gizmos.gizmo_options import TextInput, ToggleSwitch, SelectInput
# CityWater
# TODO: Move epanet helpers into organization organization/services/methods
from tethysapp.epanet.app import LICENSE_DISPLAY_NAMES
from tethysapp.epanet.lib.storage_helpers import DEFAULT_STORAGE
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services._app_users import update_user_permissions


class ModifyOrganization(TethysController):
    """
    Controller for modify_organization page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Add Organization'
    template_name = 'atcore/app_users/modify_organization.html'
    http_method_names = ['get', 'post']

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
        return self._handle_modify_user_requests(request)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        return self._handle_modify_user_requests(request, *args, **kwargs)

    # @method_decorator(active_user_required) #TODO: Generalize active_user_required
    @permission_required('modify_organizations')
    def _handle_modify_user_requests(self, request, organization_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        from django.contrib.auth.models import User
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        UR_APP_ADMIN = 'app_admin'  # TODO: Handle constants
        make_session = self.get_sessionmaker()

        # Defaults
        valid = True
        organization_name = ""
        selected_projects = []
        selected_owner = ""
        selected_license = ""
        is_active = True
        organization_name_error = ""
        owner_error = ""
        old_license = None

        # Permissions
        user_project_session = SessionMaker()
        can_create_enterprise = has_permission(request, 'modify_enterprise_organizations')
        can_create_professional = can_create_client_organizations_at_level(user_project_session, request,
                                                                           ACCESS_PROFESSIONAL)
        can_create_advanced = can_create_client_organizations_at_level(user_project_session, request, ACCESS_ADVANCED)
        can_create_standard = can_create_client_organizations_at_level(user_project_session, request, ACCESS_STANDARD)
        user_project_session.close()

        # Only allow users with correct permissions to create enterprise organizations
        license_options = []

        if can_create_standard:
            license_options.append((LICENSE_DISPLAY_NAMES[ACCESS_STANDARD], ACCESS_STANDARD))

        if can_create_advanced:
            license_options.append((LICENSE_DISPLAY_NAMES[ACCESS_ADVANCED], ACCESS_ADVANCED))

        if can_create_professional:
            license_options.append((LICENSE_DISPLAY_NAMES[ACCESS_PROFESSIONAL], ACCESS_PROFESSIONAL))

        if can_create_enterprise:
            license_options.append((LICENSE_DISPLAY_NAMES[ACCESS_ENTERPRISE], ACCESS_ENTERPRISE))

        # Process next
        next_arg = request.GET.get('next', "")

        if next_arg == 'manage-users':
            next_controller = 'epanet:manage_users'
        else:
            next_controller = 'epanet:manage_organizations'

        # If and ID is provided, then we are editing an existing consultant
        editing = organization_id is not None

        # Don't have the ability to create more organizations
        if not editing and not can_create_standard and not can_create_professional:
            messages.error(request, "We're sorry, but you are unable to create new organizations at this time.")
            return redirect(reverse('epanet:manage_organizations'))

        if editing:
            # Initialize the parameters from the existing consultant
            edit_session = SessionMaker()

            organization = edit_session.query(Organization).get(organization_id)
            organization_name = organization.name
            old_license = organization.access_level
            selected_license = organization.access_level
            is_active = organization.active

            # Organization options
            old_license_option = (LICENSE_DISPLAY_NAMES[old_license], old_license)
            if old_license_option not in license_options:
                license_options.append(old_license_option)

            if organization.type == ENTERPRISE_ORG_TYPE:
                license_options = (
                    (LICENSE_DISPLAY_NAMES[ACCESS_ENTERPRISE], ACCESS_ENTERPRISE),
                )

            for project in organization.user_projects:
                selected_projects.append(str(project.id))

            if organization.type == CLIENT_ORG_TYPE and len(organization.owners) > 0:
                selected_owner = str(organization.owners[0].id)

            edit_session.close()

        # Process form submission
        if request.POST and 'modify-organization-submit' in request.POST:
            # Validate the form
            organization_name = request.POST.get('organization-name', "")
            selected_projects = request.POST.getlist('organization-projects')
            selected_owner = request.POST.get('organization-owner', "")
            selected_license = request.POST.get('organization-type', "")
            is_active = True if request.POST.get('organization-status') == 'on' else False
            print(request.POST)

            # Organization name is required
            if organization_name == "":
                valid = False
                organization_name_error = "Name is required."

            # Client type organizations must have an owner
            if len(selected_owner) < 1 and selected_license in CLIENT_ACCESS_LEVELS:
                valid = False
                owner_error = "You must assign the organization to at least one owner organization."

            if valid:
                create_session = SessionMaker()

                # Lookup existing organization
                if editing:
                    organization = create_session.query(Organization).get(organization_id)
                    organization.name = organization_name
                    organization.user_projects = []
                    organization.active = is_active

                    # Reset owners on client organizations and set access level
                    if organization.type == CLIENT_ORG_TYPE:
                        organization.owners = []
                        organization.access_level = selected_license

                # Create new organization
                else:
                    print('License: {}'.format(selected_license))
                    if selected_license in CLIENT_ACCESS_LEVELS:
                        organization = ClientOrganization(
                            name=organization_name,
                            type=CLIENT_ORG_TYPE
                        )
                        organization.access_level = selected_license

                    elif selected_license == ACCESS_ENTERPRISE:
                        organization = EnterpriseOrganization(
                            name=organization_name,
                            type=ENTERPRISE_ORG_TYPE
                        )
                        organization.access_level = selected_license
                    else:
                        messages.error(request, 'An error occurred during organization creation. Please try again.')
                        create_session.close()
                        return redirect(reverse(next_controller))

                    # Add addon defaults
                    organization.addons = json.dumps(get_default_addons_dict())
                    create_session.add(organization)

                # Storage
                if not editing:
                    organization.storage = DEFAULT_STORAGE[selected_license]

                # Add projects
                for user_project_id in selected_projects:
                    user_project = create_session.query(UserProject).get(user_project_id)
                    organization.user_projects.append(user_project)

                # Add owners
                if organization.type == CLIENT_ORG_TYPE and selected_owner:
                    owner = create_session.query(Organization).get(selected_owner)
                    if owner:
                        organization.owners.append(owner)

                modify_account_status_of_unique_users_of_organization(create_session, organization)
                if organization.type == ENTERPRISE_ORG_TYPE and not is_active:
                    for client_org in organization.clients:
                        client_org.active = False
                        modify_account_status_of_unique_users_of_organization(create_session, client_org)

                create_session.commit()

                # Update organization member permissions if license changed
                if selected_license != old_license:
                    for member in organization.users:
                        django_user = member.get_django_user()
                        update_user_permissions(create_session, django_user)

                create_session.close()

                # Redirect
                return redirect(reverse(next_controller))

        # Define form
        organization_name_input = TextInput(
            display_text='Name',
            name='organization-name',
            initial=organization_name,
            error=organization_name_error
        )

        organization_type_select = SelectInput(
            display_text='License',
            name='organization-type',
            multiple=False,
            disabled=False,
            options=license_options,
            initial=selected_license
        )

        # Populate users select box
        session = SessionMaker()

        # Populate projects select box
        projects = get_user_projects(session, request)
        project_options = [(project.name, str(project.id)) for project in projects if not project.is_deleting()]

        # Sort the project options
        project_select = SelectInput(
            display_text='Projects (Optional)',
            name='organization-projects',
            multiple=True,
            options=project_options,
            initial=selected_projects
        )

        # Populate owner select box
        owner_options, license_to_owner_mapping = get_owner_options_and_mapping(session, request, license_options)
        if len(owner_options) > 0 and not selected_owner:
            selected_owner = owner_options[0][1]

        owner_select = SelectInput(
            display_text='Owner',
            name='organization-owner',
            multiple=False,
            options=owner_options,
            error=owner_error,
            initial=selected_owner
        )
        print(owner_options)
        print(selected_owner)

        organization_status_toggle = ToggleSwitch(
            display_text='Status',
            name='organization-status',
            on_label='Active',
            off_label='Inactive',
            on_style='primary',
            off_style='default',
            initial=is_active,
            size='medium'
        )

        session.close()

        context = {
            'action': 'New',
            'editing': editing,
            'organization_name_input': organization_name_input,
            'organization_type_select': organization_type_select,
            'owner_select': owner_select,
            'project_select': project_select,
            'next_controller': next_controller,
            'license_to_owner_mapping': dumps(license_to_owner_mapping),
            'organization_status_toggle': organization_status_toggle
        }

        return render(request, 'atcore/app_users/modify_user.html', context)
