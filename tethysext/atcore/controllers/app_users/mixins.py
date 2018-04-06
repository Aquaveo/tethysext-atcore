"""
********************************************************************************
* Name: mixins.py
* Author: nswain
* Created On: April 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.app_users import AppUser, Organization, Resource


class AppUsersControllerMixin:
    _AppUser = AppUser
    _Organization = Organization
    _Resource = Resource
    _app = None
    _persistent_store_name = ''

    def get_app_user_model(self):
        return self._AppUser

    def get_organization_model(self):
        return self._Organization

    def get_resource_model(self):
        return self._Resource

    def get_sessionmaker(self):
        if not self._app:
            raise NotImplementedError('get_sessionmaker method not implemented.')

        return self._app.get_persistent_store_database(self._persistent_store_name, as_sessionmaker=True)
