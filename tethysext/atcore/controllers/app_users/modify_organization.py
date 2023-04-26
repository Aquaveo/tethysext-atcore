"""
********************************************************************************
* Name: modify_organization
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import traceback
import logging
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
from tethysext.atcore.controllers.app_users.mixins import MultipleResourcesViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.exceptions import ATCoreException

log = logging.getLogger(f'tethys.{__name__}')


class ModifyOrganization(MultipleResourcesViewMixin):
    """
    Controller for modify_organization page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Add Organization'
    template_name = 'atcore/app_users/modify_organization.html'
    base_template = 'atcore/app_users/base.html'
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
        _Resources = self.get_resource_models()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # Defaults
        valid = True
        organization = None
        context = dict()
        organization_name = ""
        selected_resources = {_Resource.SLUG: [] for _Resource in _Resources}
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

        # Only allow users with correct custom_permissions to create consultant organizations
        license_options = []
        for license in licenses_can_assign:
            license_options.append(
                (_Organization.LICENSES.get_display_name_for(license), license)
            )

        # Process next
        next_arg = request.GET.get('next', "")
        active_app = get_active_app(request)
        app_namespace = active_app.url_namespace

        if next_arg == 'manage-users':
            next_controller = '{}:app_users_manage_users'.format(app_namespace)
        elif next_arg == 'manage-resources':
            next_controller = f'{app_namespace}:{_Resource.SLUG}_manage_resources'
        else:
            next_controller = '{}:app_users_manage_organizations'.format(app_namespace)

        # If and ID is provided, then we are editing an existing consultant
        editing = organization_id is not None
        creating = not editing

        try:
            # Don't have the ability to create more organizations
            if creating and not licenses_can_assign:
                raise ATCoreException("We're sorry, but you are unable to create new organizations at this time.")

            if editing:
                # Initialize the parameters from the existing consultant
                try:
                    organization = session.query(_Organization). \
                        filter(_Organization.id == organization_id). \
                        one()

                except (StatementError, NoResultFound):
                    raise ATCoreException('Unable to find the organization.')

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

                # Ensure consultant users cannot change their license on their own.
                if not has_permission(request, 'assign_any_license') \
                        and organization.license == _Organization.LICENSES.CONSULTANT:
                    license_options = (
                        (
                            _Organization.LICENSES.get_display_name_for(_Organization.LICENSES.CONSULTANT),
                            _Organization.LICENSES.CONSULTANT
                        ),
                    )

                # Get resources assigned to the organization
                for resource in organization.resources:
                    if resource.SLUG in selected_resources:
                        selected_resources[resource.SLUG].append(str(resource.id))

                # Determine if current user is a member of the organization
                am_member = organization.is_member(request_app_user)

            # Process form submission
            if request.POST and 'modify-organization-submit' in request.POST:
                # Validate the form
                post_params = request.POST
                organization_name = post_params.get('organization-name', "")
                selected_consultant = post_params.get('organization-consultant', "")
                selected_license = post_params.get('organization-license', "")

                # Process resource select params
                for _Resource in _Resources:
                    selected_resources[_Resource.SLUG].extend(
                        post_params.getlist(f'organization-resources-{_Resource.SLUG}'
                    ))

                if not am_member:
                    is_active = post_params.get('organization-status') == 'on'

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

                # Validate custom fields
                custom_valid, custom_fields_errors = self.validate_custom_fields(post_params)
                context.update(custom_fields_errors)

                if valid and custom_valid:
                    # Lookup existing organization and assign/reset fields
                    if editing:
                        organization = session.query(_Organization).get(organization_id)
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
                        session.add(organization)

                    # Add resources
                    for _Resource in _Resources:
                        for resource_id in selected_resources[_Resource.SLUG]:
                            resource = session.query(_Resource).get(resource_id)
                            organization.resources.append(resource)

                    # Assign consultant
                    if selected_consultant:
                        consultant = session.query(_Organization).get(selected_consultant)
                        organization.consultant = consultant
                    else:
                        organization.consultant = None

                    # Update user account active status
                    organization.update_member_activity(session, request)

                    # Make clients inactive as well if inactive
                    if not is_active:
                        for client_org in organization.clients:
                            client_org.active = False
                            client_org.update_member_activity(session, request)

                    session.commit()

                    # Update organization member custom_permissions if license changed
                    if selected_license != old_license:
                        permissions_manager = self.get_permissions_manager()
                        for member in organization.members:
                            member.update_permissions(session, request, permissions_manager)

                    # Call post processing hook
                    self.handle_organization_finished_processing(
                        session, request, request_app_user, organization, editing
                    )

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
            request_app_user = _AppUser.get_app_user_from_request(request, session)

            # Populate resources select box
            resources = request_app_user.get_resources(session, request, for_assigning=True)

            # Group resources by type
            resources_by_type = {_Resource.SLUG: [] for _Resource in _Resources}
            for resource in resources:
                if resource.SLUG in resources_by_type:
                    resources_by_type[resource.SLUG].append((resource.name, str(resource.id)))    
            
            resources_select_inputs = [
                SelectInput(
                    display_text=f'{_Resource.DISPLAY_TYPE_PLURAL} (Optional)',
                    name=f'organization-resources-{_Resource.SLUG}',
                    multiple=True,
                    options=resources_by_type[_Resource.SLUG],
                    initial=selected_resources[_Resource.SLUG]
                ) 
                for _Resource in _Resources
            ]

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
                size='medium',
            )

            license_to_consultant_map = self.get_license_to_consultant_map(
                request, license_options, consultant_organizations
            )

            hide_consultant_licenses = self.get_hide_consultant_licenses(request)

            # Initialize custom fields
            custom_fields = self.initialize_custom_fields(session, request, organization, editing)
            context.update(custom_fields)

        except Exception as e:
            session and session.rollback()

            if type(e) is ATCoreException:
                error_message = str(e)
            else:
                traceback.print_exc()
                error_message = ("An unexpected error occurred while uploading your project. Please try again or "
                                 "contact support@aquaveo.com for further assistance.")
            log.exception(error_message)
            messages.error(request, error_message)

            # Sessions closed in finally block
            return redirect(reverse(next_controller))
        finally:
            session and session.close()

        context.update({
            'page_title': _Organization.DISPLAY_TYPE_SINGULAR,
            'editing': editing,
            'am_member': am_member,
            'organization_name_input': organization_name_input,
            'organization_type_select': license_select,
            'owner_select': constultant_select,
            'resources_select_inputs': resources_select_inputs,
            'next_controller': next_controller,
            'license_to_consultant_map': license_to_consultant_map,
            'hide_consultant_licenses': hide_consultant_licenses,
            'organization_status_toggle': organization_status_toggle,
            'base_template': self.base_template
        })

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

    def initialize_custom_fields(self, session, request, organization, editing):
        """
        Hook to allow for initializing custom fields.

        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            organization(Organization): The organization being created / edited.
            editing(bool): True if rendering form for editing.

        Returns:
            dict: Template context variables for defining custom fields (i.e. gizmos, initial values, etc.).
        """
        return dict()

    def validate_custom_fields(self, params):
        """
        Hook to allow for validating custom fields.

        Args:
            params: The request.POST object with values submitted by user.

        Returns:
            bool, dict: False if any custom fields invalid, Template context variables for validation feedback (i.e. error messages).
        """  # noqa: E501
        return True, dict()

    def handle_organization_finished_processing(self, session, request, request_app_user, organization, editing):
        """
        Hook to allow for post processing after the resource has finished being created or updated.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            organization(Organization): The organization being created / edited.
            editing(bool): True if editing, False if creating a new resource.
        """
        pass
