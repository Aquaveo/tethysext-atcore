from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from tethys_apps.base.controller import TethysController
from tethys_apps.decorators import permission_required
from tethys_apps.utilities import get_active_app
from tethys_gizmos.gizmo_options import TextInput, ToggleSwitch, SelectInput
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin
# from tethysext.atcore.services._app_users import update_user_permissions
from tethysext.atcore.services.app_users.decorators import active_user_required


class ModifyUser(TethysController, AppUsersControllerMixin):
    """
    Controller for modify_user page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """
    template_name = 'atcore/app_users/modify_user.html'
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
    @permission_required('modify_users')
    def _handle_modify_user_requests(self, request, user_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        from django.contrib.auth.models import User
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        make_session = self.get_sessionmaker()

        # Defaults
        valid = True
        first_name = ""
        last_name = ""
        username = ""
        username_error = ""
        is_active = True
        email = ""
        password = ""
        password_confirm = ""
        password_error = ""
        password_confirm_error = ""
        selected_role = ""
        role_select_error = ""
        selected_organizations = []
        organization_select_error = ""
        disable_role_select = False
        is_me = False

        session = make_session()
        admin_user = _AppUser.get_app_user_from_request(request, session)
        organization_options = admin_user.get_organizations(session, request, as_options=True, cascade=True)
        role_options = admin_user.get_assignable_roles(request, as_options=True)
        no_organization_roles = _AppUser.ROLES.get_no_organization_roles()
        session.close()

        # Process next
        next_arg = request.GET.get('next', "")
        active_app = get_active_app(request)
        app_namespace = active_app.namespace

        if next_arg == 'manage-organizations':
            next_controller = '{}:app_users_manage_organizations'.format(app_namespace)
        else:
            next_controller = '{}:app_users_manage_users'.format(app_namespace)

        # If an ID is provided, then we are editing an existing consultant
        editing = user_id is not None

        if editing:
            # Initialize the parameters from the existing consultant
            edit_session = make_session()

            try:
                app_user = edit_session.query(_AppUser).\
                    filter(_AppUser.id == user_id).\
                    one()

            except (StatementError, NoResultFound):
                messages.warning(request, 'The user could not be found.')
                return redirect(reverse(next_controller))

            django_user = app_user.get_django_user()
            is_me = request.user == django_user

            # Normal users are disallowed from changing their own role
            if not request.user.is_staff and app_user.username == request.user.username:
                disable_role_select = True

            first_name = django_user.first_name
            last_name = django_user.last_name
            is_active = True if app_user.is_active is None else app_user.is_active
            email = django_user.email
            username = django_user.username
            selected_role = app_user.role
            selected_organizations = []
            for organization in app_user.get_organizations(edit_session, request, cascade=False):
                selected_organizations.append(str(organization.id))

            edit_session.close()

        # Process form submission
        if request.POST and 'modify-user-submit' in request.POST:
            # Validate the form
            first_name = request.POST.get('first-name', '')
            last_name = request.POST.get('last-name', '')
            is_active = request.POST.get('user-account-status') == 'on'
            email = request.POST.get('email', "")
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password-confirm', '')
            selected_role = request.POST.get('assign-role', '')
            selected_organizations = request.POST.getlist('assign-organizations', [])

            # Validate
            # Must assign user to at least one organization
            organization_required_roles = _AppUser.ROLES.get_organization_required_roles()
            if selected_role in organization_required_roles and not selected_organizations:
                valid = False
                organization_select_error = "Must assign user to at least one organization"

            # Reset selected organization (if any) when role requires no organization
            if selected_organizations and selected_role in no_organization_roles:
                selected_organizations = []

            # Only get and validate username if creating a new user, not when editing
            if not editing:
                username = request.POST.get('username', '')

                # Must provide a username
                if not username:
                    valid = False
                    username_error = "Username is required."
                # Username must be unique
                elif User.objects.filter(username=username).exists():
                    valid = False
                    username_error = "The given username already exists. Please, choose another."
                # Username cannot contain a space
                elif ' ' in username:
                    valid = False
                    username_error = "Username cannot contain a space."

            # Must provide a password when creating a new user, otherwise password is optional
            if not editing:
                if not password:
                    valid = False
                    password_error = "Password is required."

                if not password_confirm:
                    valid = False
                    password_confirm_error = "Please confirm password."

                # Passwords must be the same
                elif password and password != password_confirm:
                    valid = False
                    password_confirm_error = "Passwords do not match."

            # However, if a password is provided when editing, validate it
            elif editing and password:
                if not password_confirm:
                    valid = False
                    password_confirm_error = "Please confirm password."

                # Passwords must be the same
                elif password and password != password_confirm:
                    valid = False
                    password_confirm_error = "Passwords do not match."

            if valid:
                modify_session = make_session()

                # Lookup existing app user and django user
                if editing:
                    app_user = modify_session.query(_AppUser).get(user_id)
                    django_user = app_user.django_user

                    # Reset organizations
                    app_user.organizations = []

                # Create new client
                else:
                    app_user = _AppUser()
                    django_user = User()

                    # Only set username if not editing (username cannot be changed, because it is an id)
                    app_user.username = username
                    django_user.username = username
                    modify_session.add(app_user)

                # Set attributes of the django user
                django_user.first_name = first_name
                django_user.last_name = last_name
                django_user.email = email
                app_user.is_active = is_active

                # Only set password if one is provided and it is valid
                if password:
                    django_user.set_password(password)

                # Update role
                if selected_role and app_user.username != request.user.username:
                    app_user.role = selected_role

                # Update organizations
                for selected_organization in selected_organizations:
                    organization = modify_session.query(_Organization).get(selected_organization)
                    app_user.organizations.append(organization)

                # Persist changes
                django_user.save()
                modify_session.commit()

                # Update user custom_permissions
                permissions_manager = self.get_permissions_manager()
                app_user.update_permissions(modify_session, request, permissions_manager)
                modify_session.close()

                # Redirect
                return redirect(reverse(next_controller))

        # Define form
        first_name_input = TextInput(
            display_text='First Name (Optional)',
            name='first-name',
            initial=first_name,
        )

        last_name_input = TextInput(
            display_text='Last Name (Optional)',
            name='last-name',
            initial=last_name,
        )

        username_input = TextInput(
            display_text='Username',
            name='username',
            initial=username,
            error=username_error,
            disabled=editing
        )

        email_input = TextInput(
            display_text='Email (Optional)',
            name='email',
            initial=email,
        )

        password_input = TextInput(
            display_text='Password' if not editing else 'Password (Optional)',
            name='password',
            initial=password,
            error=password_error,
            attributes={'type': 'password'}
        )

        confirm_password_input = TextInput(
            display_text='Confirm Password' if not editing else 'Confirm Password (Optional)',
            name='password-confirm',
            initial=password_confirm,
            error=password_confirm_error,
            attributes={'type': 'password'}
        )

        user_account_status_toggle = ToggleSwitch(
            display_text='Status',
            name='user-account-status',
            on_label='Active',
            off_label='Inactive',
            on_style='primary',
            off_style='default',
            initial=is_active,
            size='medium',
            classes='user-activity-toggle'
        )

        role_select = SelectInput(
            display_text='Role',
            name='assign-role',
            multiple=False,
            initial=selected_role,
            options=role_options,
            error=role_select_error,
            disabled=disable_role_select
        )

        organization_select = SelectInput(
            display_text='Organization(s)',
            name='assign-organizations',
            multiple=True,
            initial=selected_organizations,
            options=organization_options,
            error=organization_select_error
        )

        context = {
            'next_controller': next_controller,
            'editing': editing,
            'is_me': is_me,
            'first_name_input': first_name_input,
            'last_name_input': last_name_input,
            'username_input': username_input,
            'user_account_status_toggle': user_account_status_toggle,
            'email_input': email_input,
            'password_input': password_input,
            'confirm_password_input': confirm_password_input,
            'role_select': role_select,
            'organization_select': organization_select,
            'no_organization_roles': no_organization_roles
        }
        return render(request, self.template_name, context)
