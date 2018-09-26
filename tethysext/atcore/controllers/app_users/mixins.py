"""
********************************************************************************
* Name: mixins.py
* Author: nswain
* Created On: April 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.shortcuts import reverse, redirect
from django.contrib import messages
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


class AppUsersControllerMixin:
    _AppUser = AppUser
    _Organization = Organization
    _Resource = Resource
    _PermissionsManager = AppPermissionsManager
    _app = None
    _persistent_store_name = ''

    def get_app(self):
        return self._app

    def get_app_user_model(self):
        return self._AppUser

    def get_organization_model(self):
        return self._Organization

    def get_resource_model(self):
        return self._Resource

    def get_permissions_manager(self):
        return self._PermissionsManager(self._app.namespace)

    def get_sessionmaker(self):
        if not self._app:
            raise NotImplementedError('get_sessionmaker method not implemented.')

        return self._app.get_persistent_store_database(self._persistent_store_name, as_sessionmaker=True)


class AppUsersResourceControllerMixin(AppUsersControllerMixin):

    def _get_resource(self, request, resource_id, back_controller, session=None):
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
        manage_session = False

        if not session:
            manage_session = True
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

        # TODO: Create resource controller decorator to handle permissions checks and redirects
        except (StatementError, NoResultFound):
            messages.warning(request, 'The {} could not be found.'.format(
                _Resource.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(reverse(back_controller))
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(reverse(back_controller))

        finally:
            if manage_session:
                session.close()

        return resource
