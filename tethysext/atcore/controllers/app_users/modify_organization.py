"""
********************************************************************************
* Name: modify_organization
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
# Tethys core
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from tethys_sdk.permissions import permission_required, has_permission
from tethys_apps.utilities import get_active_app
from tethys_gizmos.gizmo_options import TextInput, ToggleSwitch, SelectInput
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required


class ModifyOrganization(AppUsersViewMixin):
    """
    Controller for modify_organization page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Add Organization'
    template_name = 'atcore/app_users/modify_organization.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_modify_user_requests(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        return self._handle_modify_user_requests(request, *args, **kwargs)

    @active_user_required()
    @permission_required('edit_organizations', 'create_organizations', use_or=True)
    def _handle_modify_user_requests(self, request, organization_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()

        user_session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, user_session)
        user_session.close()

        # Defaults
        valid = True
        organization_name = ""
        selected_resources = []
        selected_consultant = ""
        selected_license = ""
        is_active = True
        organization_name_error = ""
        consultant_error = ""
        license_error = ""
        old_license = None
        am_member = False

        # Permissions
        licenses_can_assign = []
        for license in _Organization.LICENSES.list():
            if has_permission(request, _Organization.LICENSES.get_assign_permission_for(license)):
                licenses_can_assign.append(license)

        # Only allow users with correct custom_permissions to create enterprise organizations
        license_options = []
        for license in licenses_can_assign:
            license_options.append(
                (_Organization.LICENSES.get_display_name_for(license), license)
            )

        # Process next
        next_arg = request.GET.get('next', "")
        active_app = get_active_app(request)
        app_namespace = active_app.namespace

        if next_arg == 'manage-users':
            next_controller = '{}:app_users_manage_users'.format(app_namespace)
        elif next_arg == 'manage-resources':
            next_controller = '{}:app_users_manage_resources'.format(app_namespace)
        else:
            next_controller = '{}:app_users_manage_organizations'.format(app_namespace)

        # If and ID is provided, then we are editing an existing consultant
        editing = organization_id is not None

        # Don't have the ability to create more organizations
        if not editing and not licenses_can_assign:
            messages.error(request, "We're sorry, but you are unable to create new organizations at this time.")
            return redirect(reverse(next_controller))

        if editing:
            # Initialize the parameters from the existing consultant
            edit_session = make_session()

            try:
                organization = edit_session.query(_Organization). \
                    filter(_Organization.id == organization_id). \
                    one()

            except (StatementError, NoResultFound):
                messages.warning(request, 'The organization could not be found.')
                edit_session.close()
                return redirect(reverse(next_controller))

            organization_name = organization.name
            old_license = organization.license
            selected_license = organization.license
            selected_consultant = str(organization.consultant.id) if organization.consultant else ""
            is_active = organization.active

            # Ensure old license option is in license options
            old_license_option = (
                _Organization.LICENSES.get_display_name_for(old_license),
                old_license
            )

            if old_license_option not in license_options:
                license_options.append(old_license_option)

            # Ensure enterprise users cannot change their license on their own.
            if not has_permission(request, 'assign_any_license') \
                    and organization.license == _Organization.LICENSES.ENTERPRISE:
                license_options = (
                    (
                        _Organization.LICENSES.get_display_name_for(_Organization.LICENSES.ENTERPRISE),
                        _Organization.LICENSES.ENTERPRISE
                    ),
                )

            for resource in organization.resources:
                selected_resources.append(str(resource.id))

            # Determine if current user is a member of the organization
            am_member = organization.is_member(request_app_user)

            edit_session.close()

        # Process form submission
        if request.POST and 'modify-organization-submit' in request.POST:
            # Validate the form
            organization_name = request.POST.get('organization-name', "")
            selected_resources = request.POST.getlist('organization-resources')
            selected_consultant = request.POST.get('organization-consultant', "")
            selected_license = request.POST.get('organization-license', "")

            if not am_member:
                is_active = request.POST.get('organization-status') == 'on'

            # Organization name is required
            if organization_name == "":
                valid = False
                organization_name_error = "Name is required."

            # Validate license
            if not selected_license or not _Organization.LICENSES.is_valid(selected_license):
                valid = False
                license_error = "You must assign a valid license to the organization."

            # Validate license assign permission
            assign_permission = _Organization.LICENSES.get_assign_permission_for(selected_license)
            if not has_permission(request, assign_permission) and selected_license != old_license:
                valid = False
                license_error = "You do not have permission to assign this license to this organization."

            # Validate consultant
            if not request_app_user.is_staff() and not selected_consultant \
                    and _Organization.LICENSES.must_have_consultant(selected_license):
                valid = False
                consultant_error = "You must assign the organization to at least one consultant organization."

            if selected_consultant and not _Organization.LICENSES.can_have_consultant(selected_license):
                selected_consultant = ""

            if valid:
                create_session = make_session()

                # Lookup existing organization and assign/reset fields
                if editing:
                    organization = create_session.query(_Organization).get(organization_id)
                    organization.name = organization_name
                    organization.license = selected_license
                    organization.active = is_active
                    organization.resources = []

                # Create new organization
                else:
                    organization = _Organization(
                        name=organization_name,
                        license=selected_license,
                        active=is_active
                    )
                    create_session.add(organization)

                # Add resources
                for resource in selected_resources:
                    resource = create_session.query(_Resource).get(resource)
                    organization.resources.append(resource)

                # Assign consultant
                if selected_consultant:
                    consultant = create_session.query(_Organization).get(selected_consultant)
                    organization.consultant = consultant
                else:
                    organization.consultant = None

                # Update user account active status
                organization.update_member_activity(create_session, request)

                # Make clients inactive as well if inactive
                if not is_active:
                    for client_org in organization.clients:
                        client_org.active = False
                        client_org.update_member_activity(create_session, request)

                create_session.commit()

                # Update organization member custom_permissions if license changed
                if selected_license != old_license:
                    permissions_manager = self.get_permissions_manager()
                    for member in organization.members:
                        member.update_permissions(create_session, request, permissions_manager)

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

        license_select = SelectInput(
            display_text='License',
            name='organization-license',
            multiple=False,
            disabled=False,
            options=license_options,
            initial=selected_license,
            error=license_error
        )

        # Populate users select box
        session = make_session()

        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # Populate projects select box
        resources = request_app_user.get_resources(session, request, for_assigning=True)

        resource_options = [(r.name, str(r.id)) for r in resources]

        # Sort the project options
        project_select = SelectInput(
            display_text=_Resource.DISPLAY_TYPE_PLURAL + ' (Optional)',
            name='organization-resources',
            multiple=True,
            options=resource_options,
            initial=selected_resources
        )

        # Populate owner select box
        consultant_options = request_app_user.get_organizations(session, request, as_options=True, consultants=True)
        consultant_organizations = request_app_user.get_organizations(session, request, consultants=True)

        # Remove this organization for consultant options if present
        if editing:
            temp_consultant_options = []
            for consultant_option in consultant_options:
                if consultant_option[1] != str(organization.id):
                    temp_consultant_options.append(consultant_option)

            consultant_options = temp_consultant_options

        # Prepend None option
        consultant_options.insert(0, ('None', ''))

        # Default selected consultant if none selected yet.
        if len(consultant_options) > 0 and not selected_consultant:
            selected_consultant = consultant_options[0][1]

        constultant_select = SelectInput(
            display_text='Consultant',
            name='organization-consultant',
            multiple=False,
            options=consultant_options,
            error=consultant_error,
            initial=selected_consultant
        )

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

        license_to_consultant_map = self.get_license_to_consultant_map(
            request, license_options, consultant_organizations
        )

        hide_consultant_licenses = self.get_hide_consultant_licenses(request)

        session.close()

        context = {
            'page_title': _Organization.DISPLAY_TYPE_SINGULAR,
            'editing': editing,
            'am_member': am_member,
            'organization_name_input': organization_name_input,
            'organization_type_select': license_select,
            'owner_select': constultant_select,
            'project_select': project_select,
            'next_controller': next_controller,
            'license_to_consultant_map': license_to_consultant_map,
            'hide_consultant_licenses': hide_consultant_licenses,
            'organization_status_toggle': organization_status_toggle
        }

        return render(request, self.template_name, context)

    def get_license_to_consultant_map(self, request, license_options, consultant_organizations):
        """
        Build map of organizations that can still add clients for each of the license options.
        Args:
            request(django.request): Django request object
            license_options(list): List of license tuples e.g.: [('Standard': 'standard'), ('Advanced', 'advanced')]
            consultant_organizations(list<Organization>): list of consultant organitions.
        Returns:
            dict: liceses as keys, and a list of organizations that can add clients of that license as values.
        """
        make_session = self.get_sessionmaker()
        session = make_session()
        license_to_consultant_map = {}
        _Organization = self.get_organization_model()

        for _, lic in license_options:
            # Lazy load
            if lic not in license_to_consultant_map:
                license_to_consultant_map[lic] = [] if _Organization.LICENSES.must_have_consultant(lic) else ['']

            # Check each organization to see if it can still add clients of the given license.
            for organization in consultant_organizations:
                if organization.can_add_client_with_license(session, request, lic):
                    license_to_consultant_map[lic].append(str(organization.id))

        session.close()
        return license_to_consultant_map

    def get_hide_consultant_licenses(self, request):
        """
        Get a list of licenses that will cause the consultant field to be hidden/disabled.
        Args:
            request(django.request): Django request object

        Returns:
            list: List of licenses will cause the consultant field to be hidden/disabled.
        """
        hide_consultant_licenses = []
        _Organization = self.get_organization_model()

        for license in _Organization.LICENSES.list():
            if not _Organization.LICENSES.can_have_consultant(license):
                hide_consultant_licenses.append(license)

        return hide_consultant_licenses
