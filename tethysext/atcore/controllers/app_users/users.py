"""
********************************************************************************
* Name: users.py
* Author: nswain
* Created On: March, 19, 2018
* Copyright: (c) Aquaveo 2018
* License: 
********************************************************************************
"""
# Django
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
# Tethys core
from tethys_sdk.gizmos import TextInput, SelectInput, ToggleSwitch
from tethys_sdk.permissions import has_permission, permission_required
from tethys_sdk.base import TethysController
# ATCore
from tethysext.atcore.models.app_users import AppUser, Organization
# App User Services
from tethysext.atcore.services.app_users import get_display_name_for_django_user, get_assignable_roles, get_role, \
    remove_all_epanet_permissions_groups, get_user_peers, get_user_organizations, update_user_permissions, \
    get_all_permissions_groups_for_user, assign_user_permission, active_user_required


class ManageUsers(TethysController):
    """
    Controller for manage_users page.

    GET: Render list of all users.
    DELETE: Delete/remove user.
    """

    page_title = 'User Accounts'
    template_name = 'atcore/app_users/manage_users.html'
    http_method_names = ['get', 'delete']

    def get_app_user_model(self):
        return AppUser

    def get_organization_model(self):
        return Organization

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
        elif action == 'remove':
            return self._handle_remove(request, user_id)

        return JsonResponse({'success': False, 'error': 'Invalid action: {}'.format(action)})

    # @method_decorator(active_user_required) #TODO: Generalize active_user_required
    @permission_required('view_users')
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        Session = self.get_sessionmaker()
        session = Session()

        # List users
        user_cards = []

        # GET params
        params = request.GET
        page = int(params.get('page', 1))
        results_per_page = int(params.get('show', 10))

        # App admins can see all users of the portal
        if has_permission(request, 'view_all_users'):
            # Django users
            app_users = session.query(AppUser).all()
        else:
            # All others can manage users that belong to their organizations
            app_users = get_user_peers(session, request, include_self=False, cascade=True)

        app_users = sorted(app_users, key=lambda u: u.username)

        permission_value_dict = {'standard viewer': 0, 'standard admin': 1,
                                 'professional viewer': 2, 'professional admin': 3,
                                 'enterprise viewer': 4, 'enterprise admin': 5,
                                 'app admin': 100, 'staff': 1000}

        me = session.query(AppUser).filter(AppUser.username == request.user.username).one_or_none()

        if me:
            app_users.insert(0, me)
            request_permission_value = None

        for app_user in app_users:
            django_user = app_user.get_django_user()

            # This should only happen with staff users...
            if django_user is None:
                continue

            is_me = django_user == request.user

            editable = False
            organizations = session.query(Organization.name).filter(Organization.members.contains(app_user))
            permissions_groups = get_all_permissions_groups_for_user(django_user, as_display_name=True)

            # Find permission level and decide if request.user can edit other users
            permission_value_list = [-1]
            for group in permissions_groups:
                # Ignore addon permissions groups
                if group.lower() in permission_value_dict:
                    permission_value = permission_value_dict[group.lower()]
                    permission_value_list.append(permission_value)

            if is_me:
                request_permission_value = max(permission_value_list)
            if request.user.is_staff:
                request_permission_value = permission_value_dict['staff']

            user_permission_value = max(permission_value_list)

            if request_permission_value and request_permission_value > user_permission_value:
                editable = True
            elif is_me:
                editable = True

            user_card = {
                'id': app_user.id,
                'username': app_user.username,
                'fullname': 'Me' if is_me else get_display_name_for_django_user(django_user, append_username=True),
                'email': django_user.email,
                # 'role': get_role(session, django_user, True),  # TODO: Fix once organizations is implemented
                'organizations': organizations,
                'editable': editable
            }

            user_cards.append(user_card)

        # Pagination setup
        results_per_page_options = [5, 10, 20, 40, 80, 120]
        num_users = len(user_cards)
        if num_users <= results_per_page:
            page = 1
        min_index = (page - 1) * results_per_page
        max_index = min(page * results_per_page, num_users)
        paginated_user_cards = user_cards[min_index:max_index]
        enable_next_button = max_index < num_users
        enable_previous_button = min_index > 0

        context = {
            'page_title': self.page_title,
            'user_cards': paginated_user_cards,
            'show_new_button': has_permission(request, 'modify_users'),
            'show_action_buttons': has_permission(request, 'modify_users'),
            'show_remove_button': request.user.is_staff,
            'show_add_existing_button': request.user.is_staff,
            'show_manage_users_link': has_permission(request, 'view_users'),
            'show_manage_organizations_link': has_permission(request, 'view_organizations'),
            'pagination_info': {
                'num_results': num_users,
                'result_name': 'users',
                'page': page,
                'min_showing': min_index + 1 if max_index > 0 else 0,
                'max_showing': max_index,
                'next_page': page + 1,
                'previous_page': page - 1,
                'enable_next_button': enable_next_button,
                'enable_previous_button': enable_previous_button,
                'hide_buttons': page == 1 and max_index == num_users,
                'show': results_per_page,
                'results_per_page_options': [x for x in results_per_page_options if x <= num_users],
                'hide_results_per_page_options': num_users <= results_per_page_options[0],
            },
        }

        session.close()

        return render(request, self.template_name, context)

    @permission_required('modify_users')
    def _handle_delete(self, request, user_id):
        """
        Handle delete user requests.
        """
        AppUser = self.get_app_user_model()
        SessionMaker = self.get_sessionmaker()

        json_response = {'success': True}
        session = SessionMaker()
        try:
            app_user = session.query(AppUser).get(user_id)
            django_user = app_user.get_django_user()
            django_user.delete()
            session.delete(app_user)
            session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}
        session.close()
        return JsonResponse(json_response)

    @method_decorator(staff_member_required)
    def _handle_remove(self, request, user_id):
        """
        Handle remove user requests.
        Args:
            request: Request object.
            user_id: id of user to delete.

        Returns:
            JsonResponse: success and error.
        """
        AppUser = self.get_app_user_model()
        SessionMaker = self.get_sessionmaker()

        json_response = {'success': True}
        session = SessionMaker()
        try:
            app_user = session.query(AppUser).get(user_id)
            django_user = app_user.get_django_user()
            remove_all_epanet_permissions_groups(django_user)
            django_user.save()
            session.delete(app_user)
            session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}
        session.close()
        return JsonResponse(json_response)


class ModifyUser(TethysController):
    """
    Controller for modify_user page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Add User'
    template_name = 'atcore/app_users/modify_user.html'
    http_method_names = ['get', 'post']

    def get_app_user_model(self):
        return AppUser

    def get_organization_model(self):
        return Organization

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
    @permission_required('modify_users')
    def _handle_modify_user_requests(self, request, user_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        from django.contrib.auth.models import User
        AppUser = self.get_app_user_model()
        Organization = self.get_organization_model()
        UR_APP_ADMIN = 'foo'  # TODO: Handle constants
        SessionMaker = self.get_sessionmaker()

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

        # Process next
        next_arg = request.GET.get('next', "")

        if next_arg == 'manage-organizations':
            next_controller = 'epanet:manage_organizations'
        else:
            next_controller = 'epanet:manage_users'

        # If an ID is provided, then we are editing an existing consultant
        editing = user_id is not None

        if editing:
            # Initialize the parameters from the existing consultant
            edit_session = SessionMaker()

            app_user = edit_session.query(AppUser).get(user_id)
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

            # Get organizations of user
            for organization in app_user.organizations:
                selected_organizations.append(str(organization.id))

            edit_session.close()

        # Process form submission
        if request.POST and 'modify-user-submit' in request.POST:
            # Validate the form
            first_name = request.POST.get('first-name', '')
            last_name = request.POST.get('last-name', '')
            is_active = request.POST.get('user-account-status', 'on') == 'on'
            email = request.POST.get('email', "")
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password-confirm', '')
            selected_role = request.POST.get('assign-role', '')
            selected_organizations = request.POST.getlist('assign-organizations')

            # Validate
            # Must assign user to at least one organization
            if selected_role != UR_APP_ADMIN and len(selected_organizations) < 1:
                valid = False
                organization_select_error = "Must assign user to at least one organization"

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
                modify_session = SessionMaker()

                # Lookup existing app user and django user
                if editing:
                    app_user = modify_session.query(AppUser).get(user_id)
                    django_user = app_user.get_django_user()

                    # Reset organizations
                    app_user.organizations = []

                # Create new client
                else:
                    app_user = AppUser()
                    django_user = User()

                    # Only set username if not editing (username cannot be changed, because it is an id)
                    app_user.username = username
                    django_user.username = username

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
                    organization = modify_session.query(Organization).get(selected_organization)
                    app_user.organizations.append(organization)

                # Persist changes
                django_user.save()
                modify_session.commit()

                # Update user permissions
                update_user_permissions(modify_session, django_user)
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

        user_account_status_toggle = ToggleSwitch(display_text='Status',
                                                  name='user-account-status',
                                                  on_label='Active',
                                                  off_label='Inactive',
                                                  on_style='primary',
                                                  off_style='default',
                                                  initial=is_active,
                                                  size='medium',
                                                  classes='user-activity-toggle'
                                                  )

        role_options = get_assignable_roles(request, as_options=True)

        role_select = SelectInput(
            display_text='Role',
            name='assign-role',
            multiple=False,
            initial=selected_role,
            options=role_options,
            error=role_select_error,
            disabled=disable_role_select
        )

        session = SessionMaker()
        organization_options = get_user_organizations(session, request, as_options=True, cascade=True)
        session.close()

        organization_select = SelectInput(
            display_text='Organization(s)',
            name='assign-organizations',
            multiple=True,
            initial=selected_organizations,
            options=organization_options,
            error=organization_select_error
        )

        context = {
            'action': 'New',
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
        }
        return render(request, 'atcore/app_users/modify_user.html', context)


class AddExistingUser(TethysController):
    """
    Controller for add_existing_user page.

    GET: Render form for adding an existing user from the Django user database.
    POST: Handle form submission to add an existing a new user from the Django user database.
    """
    page_title = 'Add Existing User'
    template_name = 'atcore/app_users/add_existing_user.html'
    http_method_names = ['get', 'post']

    def get_app_user_model(self):
        return AppUser

    def get_organization_model(self):
        return Organization

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

    @method_decorator(staff_member_required)
    def _handle_modify_user_requests(self, request, user_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        from django.contrib.auth.models import User
        AppUser = self.get_app_user_model()
        Organization = self.get_organization_model()
        SessionMaker = self.get_sessionmaker()
        UR_APP_ADMIN = 'app_admin'  # TODO: Generalize this variable.

        valid = True
        selected_portal_users = []
        selected_portal_users_error = ""
        selected_role = ""
        role_select_error = ""
        selected_organizations = []
        organization_select_error = ""

        # Process form request
        if request.POST and 'add-existing-user-submit' in request.POST:
            selected_portal_users = request.POST.getlist('portal-users')
            selected_role = request.POST.get('assign-role', '')
            selected_organizations = request.POST.getlist('assign-organizations')

            # Validate
            if not selected_role:
                valid = False
                role_select_error = "A role must be assigned to user."

            if len(selected_portal_users) < 1:
                valid = False
                selected_portal_users_error = "Must select at least one user."

            # Must assign user to at least one organization
            if selected_role != UR_APP_ADMIN and len(selected_organizations) < 1:
                valid = False
                organization_select_error = "Must assign user to at least one organization"

            if valid:
                # Create a new AppUser for each django user and associate it with the Django users with the username
                create_session = SessionMaker()

                for django_username in selected_portal_users:
                    app_user = AppUser(
                        username=django_username,
                    )

                    django_user = app_user.get_django_user()

                    # To be safe we will remove all epanet roles that may
                    # already be applied to the user to give us a clean slate
                    remove_all_epanet_permissions_groups(django_user)

                    if selected_role and app_user.username != request.user.username:
                        app_user.role = selected_role

                    # Add user to selected organizations and assign permissions
                    if selected_role != UR_APP_ADMIN:
                        for organization_id in selected_organizations:
                            organization = create_session.query(Organization).get(organization_id)
                            app_user.organizations.append(organization)
                            assign_user_permission(django_user, app_user.role, organization.access_level)

                    # If user has app admin role, assign app admin permission
                    else:
                        assign_user_permission(django_user, app_user.role)

                    create_session.add(app_user)

                create_session.commit()
                create_session.close()
                return redirect(reverse('epanet:manage_users'))

        # Get App Users
        session = SessionMaker()
        app_users = session.query(AppUser).all()

        # Setup portal users select
        all_app_usernames = [app_user.username for app_user in app_users]
        all_django_users = User.objects.all()
        portal_users_options = []

        # Options include all users not assigned to the app already
        for django_user in all_django_users:
            if django_user.username not in all_app_usernames:
                portal_users_options.append(
                    (get_display_name_for_django_user(django_user, append_username=True), django_user.username)
                )

        portal_users_options = sorted(portal_users_options, key=lambda u: u[0])

        portal_users_select = SelectInput(
            display_text='Existing User(s)',
            name='portal-users',
            multiple=True,
            initial=selected_portal_users,
            options=portal_users_options,
            error=selected_portal_users_error
        )

        role_options = get_assignable_roles(request, as_options=True)

        role_select = SelectInput(
            display_text='Role',
            name='assign-role',
            multiple=False,
            initial=selected_role,
            options=role_options,
            error=role_select_error
        )

        organization_options = get_user_organizations(session, request, as_options=True, cascade=True)

        organization_select = SelectInput(
            display_text='Organization(s)',
            name='assign-organizations',
            multiple=True,
            initial=selected_organizations,
            options=organization_options,
            error=organization_select_error
        )

        session.close()
        context = {
            'portal_users_select': portal_users_select,
            'role_select': role_select,
            'organization_select': organization_select,
        }
        return render(request, 'epanet/manage/add_existing_user.html', context)
