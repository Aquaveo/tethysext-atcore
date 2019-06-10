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
from tethys_sdk.permissions import has_permission, permission_required
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.services.paginate import paginate


class ManageUsers(AppUsersViewMixin):
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

    @active_user_required()
    @permission_required('view_users')
    def _handle_get(self, request):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        permissions_manager = self.get_permissions_manager()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # List users
        user_cards = []

        # GET params
        params = request.GET
        page = int(params.get('page', 1))
        results_per_page = int(params.get('show', 10))

        # App admins can see all users of the portal
        if has_permission(request, 'view_all_users'):
            # Django users
            app_users = session.query(_AppUser).filter(_AppUser.username != request_app_user.username).all()
        else:
            # All others can manage users that belong to their organizations or organizations they consult
            app_users = request_app_user.get_peers(session, request, include_self=False, cascade=True)

        app_users = sorted(app_users, key=lambda u: u.username)

        # Handle how current user is shown (me)
        if not request_app_user.is_staff():
            app_users.insert(0, request_app_user)

        request_user_permission_rank = request_app_user.get_rank(permissions_manager)

        for app_user in app_users:
            # skip staff users
            if app_user.is_staff():
                continue

            is_me = app_user.username == request_app_user.username

            # Determine if request user can edit this user
            editable = False
            current_user_rank = app_user.get_rank(permissions_manager)

            if request_user_permission_rank and request_user_permission_rank >= current_user_rank:
                editable = True
            elif is_me:
                editable = True

            # Get organizations
            organizations = []

            if app_user.role not in self._AppUser.ROLES.get_no_organization_roles():
                organizations = app_user.get_organizations(session, request, cascade=False)

            user_card = {
                'id': app_user.id,
                'username': app_user.username,
                'fullname': 'Me' if is_me else app_user.get_display_name(append_username=True),
                'email': app_user.email,
                'active': app_user.is_active,
                'role': app_user.get_role(True),
                'organizations': organizations,
                'editable': editable
            }

            user_cards.append(user_card)

        # Generate pagination
        paginated_user_cards, pagination_info = paginate(
            objects=user_cards,
            results_per_page=results_per_page,
            page=page,
            result_name='users'
        )

        context = {
            'page_title': self.page_title,
            'base_template': self.base_template,
            'user_cards': paginated_user_cards,
            'show_new_button': has_permission(request, 'modify_users'),
            'show_action_buttons': has_permission(request, 'modify_users'),
            'show_remove_button': request.user.is_staff,
            'show_add_existing_button': request.user.is_staff,
            'show_links_to_organizations': has_permission(request, 'view_organizations'),
            'pagination_info': pagination_info,
            'show_users_link': has_permission(request, 'modify_users'),
            'show_resources_link': has_permission(request, 'view_resources'),
            'show_organizations_link': has_permission(request, 'view_organizations')
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
        permissions_manager = self.get_permissions_manager()
        make_session = self.get_sessionmaker()

        json_response = {'success': True}
        session = make_session()
        try:
            app_user = session.query(_AppUser).get(user_id)
            permissions_manager.remove_all_permissions_groups(app_user)
            session.delete(app_user)
            session.commit()
        except Exception as e:
            json_response = {'success': False,
                             'error': repr(e)}
        session.close()
        return JsonResponse(json_response)
