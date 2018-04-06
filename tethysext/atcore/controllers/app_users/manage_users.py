"""
********************************************************************************
* Name: users.py
* Author: nswain
* Created On: March 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
# Tethys core
from tethys_sdk.base import TethysController
from tethys_sdk.permissions import has_permission, permission_required
# ATCore
from tethysext.atcore.services._app_users import remove_all_epanet_permissions_groups, get_user_peers, \
                                                 get_all_permissions_groups_for_user
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin


class ManageUsers(TethysController, AppUsersControllerMixin):
    """
    Controller for manage_users page.

    GET: Render list of all users.
    DELETE: Delete/remove user.
    """

    page_title = 'User Accounts'
    template_name = 'atcore/app_users/manage_users.html'
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
        elif action == 'remove':
            return self._handle_remove(request, user_id)

        return JsonResponse({'success': False, 'error': 'Invalid action: {}'.format(action)})

    # @method_decorator(active_user_required) #TODO: Generalize active_user_required
    @permission_required('view_users')
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        make_session = self.get_sessionmaker()
        session = make_session()

        # List users
        user_cards = []

        # GET params
        params = request.GET
        page = int(params.get('page', 1))
        results_per_page = int(params.get('show', 10))

        # App admins can see all users of the portal
        if has_permission(request, 'view_all_users'):
            # Django users
            app_users = session.query(_AppUser).all()
        else:
            # All others can manage users that belong to their organizations
            app_users = get_user_peers(session, request, include_self=False, cascade=True)

        app_users = sorted(app_users, key=lambda u: u.username)

        permission_value_dict = {'standard viewer': 0, 'standard admin': 1,
                                 'professional viewer': 2, 'professional admin': 3,
                                 'enterprise viewer': 4, 'enterprise admin': 5,
                                 'app admin': 100, 'staff': 1000}

        me = _AppUser.get_app_user_from_request(request, session)

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
            organizations = session.query(_Organization.name, _Organization.id).\
                filter(_Organization.members.contains(app_user)).\
                all()
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
                'fullname': 'Me' if is_me else app_user.get_display_name(append_username=True),
                'email': django_user.email,
                'role': app_user.get_role(True),
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
            'base_template': self.base_template,
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
        _AppUser = self.get_app_user_model()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()
        try:
            app_user = session.query(_AppUser).get(user_id)
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
        _AppUser = self.get_app_user_model()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()
        try:
            app_user = session.query(_AppUser).get(user_id)
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
