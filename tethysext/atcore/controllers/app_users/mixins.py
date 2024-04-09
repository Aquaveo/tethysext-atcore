"""
********************************************************************************
* Name: base.py
* Author: nswain
* Created On: April 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.shortcuts import reverse
from django.conf import settings
from tethys_apps.utilities import get_active_app
from tethys_sdk.base import TethysController
from tethys_sdk.permissions import has_permission
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


class AppUsersViewMixin(TethysController):
    """
    Mixin for class-based views that adds convenience methods for working with the app user models.
    """
    _AppUser = AppUser
    _Organization = Organization
    _PermissionsManager = AppPermissionsManager
    _app = None
    _persistent_store_name = ''

    def get_app(self):
        return self._app

    def get_app_user_model(self):
        return self._AppUser

    def get_organization_model(self):
        return self._Organization

    def get_permissions_manager(self):
        return self._PermissionsManager(self._app.url_namespace)

    def get_sessionmaker(self):
        if not self._app:
            raise NotImplementedError('get_sessionmaker method not implemented.')

        return self._app.get_persistent_store_database(self._persistent_store_name, as_sessionmaker=True)

    def get_base_context(self, request):
        base_context = {
            'is_app_admin': has_permission(request, 'has_app_admin_role')
        }
        return base_context


class ResourceBackUrlViewMixin(AppUsersViewMixin):
    def get_resource(self, request, resource_id, session=None):
        """
        Get the resource and check permissions.

        Args:
            request: Django HttpRequest.
            resource_id: ID of the resource.
            session: SQLAlchemy session. Optional.

        Returns:
            Resource: the resource.
        """
        raise NotImplementedError('get_resource method not implemented.')

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept kwargs before calling handler method.
        """
        # Handle back_url
        self.back_url = kwargs.get('back_url', '')

        # Default to the resource details page
        if not self.back_url:
            self.back_url = self.default_back_url(
                *args,
                request=request,
                **kwargs
            )
        return super().dispatch(request, *args, **kwargs)

    def default_back_url(self, request, *args, **kwargs):
        """
        Hook for custom back url. Defaults to the resource details page.

        Returns:
            str: back url.
        """
        active_app = get_active_app(request)
        app_namespace = active_app.url_namespace
        resource_id = kwargs.get('resource_id', '')
        resource = self.get_resource(request, resource_id) if resource_id else None
        if resource:
            # Get resource_details page for the resource
            resource = self.get_resource(request, resource_id)
            back_controller = f'{app_namespace}:{resource.SLUG}_resource_details'
            return reverse(back_controller, args=(str(resource_id),))
        else:
            # If no resource_id provided, default to the index page of the app
            back_controller = f'{app_namespace}:{active_app.index}'
            return reverse(back_controller)


class ResourceViewMixin(ResourceBackUrlViewMixin):
    """
    Mixin for class-based views that adds convenience methods for working with resources.
    """
    back_url = ''
    _Resource = Resource

    def get_resource_model(self):
        return self._Resource

    def get_resource(self, request, resource_id, session=None):
        """
        Get the resource and check permissions.

        Args:
            request: Django HttpRequest.
            resource_id: ID of the resource.
            session: SQLAlchemy session. Optional.

        Returns:
            Resource: the resource.
        """
        # Setup
        _AppUser = self.get_app_user_model()
        _Resource = self.get_resource_model()
        manage_session = False

        if not session:
            manage_session = True
            make_session = self.get_sessionmaker()
            session = make_session()

        request_app_user = _AppUser.get_app_user_from_request(request, session)
        try:
            resource = session.query(_Resource).get(resource_id)

            # TODO: Let the apps check permissions so anonymous user only has access to app specific resources?
            if not getattr(settings, 'ENABLE_OPEN_PORTAL', False):
                if resource and not request_app_user.can_view(session, request, resource):
                    raise ATCoreException('You are not allowed to access this {}'.format(
                        _Resource.DISPLAY_TYPE_SINGULAR.lower()
                    ))
        finally:
            if manage_session:
                session.close()

        return resource


class MultipleResourcesViewMixin(ResourceBackUrlViewMixin):
    """
    Mixin for class-based views that adds convenience methods for working with resources.
    """
    back_url = ''
    _Resources = [Resource]

    def get_resource_models(self):
        return self._Resources

    def get_resource(self, request, resource_id, session=None):
        """
        Get the resource and check permissions.

        Args:
            request: Django HttpRequest.
            resource_id: ID of the resource.
            session: SQLAlchemy session. Optional.

        Returns:
            Resource: the resource.
        """
        # Setup
        _AppUser = self.get_app_user_model()
        _Resources = self.get_resource_models()
        manage_session = False

        if not session:
            manage_session = True
            make_session = self.get_sessionmaker()
            session = make_session()

        request_app_user = _AppUser.get_app_user_from_request(request, session)
        try:
            for _Resource in _Resources:
                resource = session.query(_Resource).get(resource_id)
                if resource:
                    break

            # TODO: Let the apps check permissions so anonymous user only has access to app specific resources?
            if not getattr(settings, 'ENABLE_OPEN_PORTAL', False):
                if resource and not request_app_user.can_view(session, request, resource):
                    raise ATCoreException('You are not allowed to access this {}'.format(
                        resource.DISPLAY_TYPE_SINGULAR.lower()
                    ))
        finally:
            if manage_session:
                session.close()

        return resource
