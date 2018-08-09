"""
********************************************************************************
* Name: resource_details.py
* Author: nswain
* Created On: April 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
# Django
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
# Tethys core
from tethys_sdk.base import TethysController
from tethys_sdk.permissions import permission_required
from tethys_apps.utilities import get_active_app
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.services.app_users.decorators import active_user_required


class ResourceDetails(TethysController, AppUsersControllerMixin):
    """
    Controller for resource_details page.

    GET: Render detail view of given resource.
    """
    template_name = 'atcore/app_users/resource_details.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get', 'delete']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request, *args, **kwargs)

    @active_user_required()
    @permission_required('view_resources')
    def _handle_get(self, request, resource_id, *args, **kwargs):
        """
        Handle get requests.
        """
        back_controller = self._get_back_controller(request)
        resource = self._get_resource(request, resource_id, back_controller)

        context = {
            'resource': resource,
            'back': back_controller
        }

        context = self.get_context(context)

        return render(request, self.template_name, context)

    def _get_back_controller(self, request):
        """
        Derive the back controller.

        Args:
            request: Django HttpRequest.

        Returns:
            str: name of the controller to return to when hitting back or on error.
        """
        # Process next
        back_arg = request.GET.get('back', "")
        active_app = get_active_app(request)
        app_namespace = active_app.namespace
        if back_arg == 'manage-organizations':
            back_controller = '{}:app_users_manage_organizations'.format(app_namespace)
        else:
            back_controller = '{}:app_users_manage_resources'.format(app_namespace)
        return back_controller

    def _get_resource(self, request, resource_id, back_controller):
        """
        Get the resource an check permissions.

        Args:
            request: Django HttpRequest.
            resource_id: ID of the resource.

        Returns:
            Resource: the resource.
        """
        # Setup
        _AppUser = self.get_app_user_model()
        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)
        resource = None

        try:
            resource = session.query(_Resource). \
                filter(_Resource.id == resource_id). \
                one()

            if not request_app_user.can_view(session, request, resource):
                raise ATCoreException('You are not allowed to access this {}'.format(
                    _Resource.DISPLAY_TYPE_SINGULAR.lower()
                ))

        except (StatementError, NoResultFound):
            messages.warning(request, 'The {} could not be found.'.format(
                _Resource.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(reverse(back_controller))
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)

        finally:
            session.close()

        return resource

    def get_context(self, context):
        """
        Hook for modifying context.

        Args:
            context(dict): context object.

        Returns:
            dict: context
        """
        return context
