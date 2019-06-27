"""
********************************************************************************
* Name: permissions_manager.py
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.services.app_users.licenses import Licenses


class AppPermissionsManager:
    _STD_U_PERMS = 'standard_user_perms'
    _STD_A_PERMS = 'standard_admin_perms'
    _ADV_U_PERMS = 'advanced_user_perms'
    _ADV_A_PERMS = 'advanced_admin_perms'
    _PRO_U_PERMS = 'professional_user_perms'
    _PRO_A_PERMS = 'professional_admin_perms'
    _ENT_U_PERMS = 'enterprise_user_perms'
    _ENT_A_PERMS = 'enterprise_admin_perms'
    _APP_A_PERMS = 'app_admin_perms'

    ROLES = Roles()
    LICENSES = Licenses()

    def __init__(self, app_namespace):
        """
        Manages custom_permissions for a given app.
        Args:
            app_namespace(str): Namespace of the app (e.g.: "my_first_app").
        """
        self.app_namespace = app_namespace

        self.STANDARD_USER_PERMS = '{}:{}'.format(self.app_namespace, self._STD_U_PERMS)
        self.STANDARD_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self._STD_A_PERMS)
        self.ADVANCED_USER_PERMS = '{}:{}'.format(self.app_namespace, self._ADV_U_PERMS)
        self.ADVANCED_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self._ADV_A_PERMS)
        self.PROFESSIONAL_USER_PERMS = '{}:{}'.format(self.app_namespace, self._PRO_U_PERMS)
        self.PROFESSIONAL_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self._PRO_A_PERMS)
        self.ENTERPRISE_USER_PERMS = '{}:{}'.format(self.app_namespace, self._ENT_U_PERMS)
        self.ENTERPRISE_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self._ENT_A_PERMS)
        self.APP_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self._APP_A_PERMS)

    def list(self, with_namespace=False):
        """
        List all permission groups.
        Returns:
            list<str>: names of all the custom_permissions groups.
        """
        if with_namespace:
            return [
                self.STANDARD_USER_PERMS,
                self.STANDARD_ADMIN_PERMS,
                self.ADVANCED_USER_PERMS,
                self.ADVANCED_ADMIN_PERMS,
                self.PROFESSIONAL_USER_PERMS,
                self.PROFESSIONAL_ADMIN_PERMS,
                self.ENTERPRISE_USER_PERMS,
                self.ENTERPRISE_ADMIN_PERMS,
                self.APP_ADMIN_PERMS
            ]
        else:
            return [
                self._STD_U_PERMS,
                self._STD_A_PERMS,
                self._ADV_U_PERMS,
                self._ADV_A_PERMS,
                self._PRO_U_PERMS,
                self._PRO_A_PERMS,
                self._ENT_U_PERMS,
                self._ENT_A_PERMS,
                self._APP_A_PERMS
            ]

    def get_permissions_group_for(self, role, license=None, **kwargs):
        """
        Get the name of the custom_permissions group for the given role, license, and other criteria.
        Args:
            role(str): Role of user.
            license(str): License of organization to which user belongs.
            **kwargs: Used for additional criteria when extending functionality of this class.

        Returns:
            str: name of permission group.
        """
        # Handle all combinations
        if role == self.ROLES.ORG_USER:
            if license == self.LICENSES.STANDARD:
                return self.STANDARD_USER_PERMS
            elif license == self.LICENSES.ADVANCED:
                return self.ADVANCED_USER_PERMS
            elif license == self.LICENSES.PROFESSIONAL:
                return self.PROFESSIONAL_USER_PERMS
            elif license == self.LICENSES.ENTERPRISE:
                return self.ENTERPRISE_USER_PERMS

        elif role == self.ROLES.ORG_ADMIN:
            if license == self.LICENSES.STANDARD:
                return self.STANDARD_ADMIN_PERMS
            elif license == self.LICENSES.ADVANCED:
                return self.ADVANCED_ADMIN_PERMS
            elif license == self.LICENSES.PROFESSIONAL:
                return self.PROFESSIONAL_ADMIN_PERMS
            elif license == self.LICENSES.ENTERPRISE:
                return self.ENTERPRISE_ADMIN_PERMS

        elif role == self.ROLES.APP_ADMIN:
            return self.APP_ADMIN_PERMS

    def get_display_name_for(self, permissions_group):
        """
        Get the display name for the given permission group.
        Args:
            permissions_group(str): name of permission group.

        Returns:
            str: Display name for the given custom_permissions group.
        """
        if permissions_group == self.STANDARD_USER_PERMS:
            return 'Standard User'
        elif permissions_group == self.STANDARD_ADMIN_PERMS:
            return 'Standard Admin'
        elif permissions_group == self.ADVANCED_USER_PERMS:
            return 'Advanced User'
        elif permissions_group == self.ADVANCED_ADMIN_PERMS:
            return 'Advanced Admin'
        elif permissions_group == self.PROFESSIONAL_USER_PERMS:
            return 'Professional User'
        elif permissions_group == self.PROFESSIONAL_ADMIN_PERMS:
            return 'Professional Admin'
        elif permissions_group == self.ENTERPRISE_USER_PERMS:
            return 'Enterprise User'
        elif permissions_group == self.ENTERPRISE_ADMIN_PERMS:
            return 'Enterprise Admin'
        elif permissions_group == self.APP_ADMIN_PERMS:
            return 'App Admin'
        return ''

    def get_rank_for(self, permissions_group):
        """
        Get the rank for the given permission group.
        Args:
            permissions_group(str): name of permission group.

        Returns:
            int: Rank for given permission group.
        """
        if permissions_group == self.STANDARD_USER_PERMS:
            return 100.0
        elif permissions_group == self.STANDARD_ADMIN_PERMS:
            return 200.0
        elif permissions_group == self.ADVANCED_USER_PERMS:
            return 300.0
        elif permissions_group == self.ADVANCED_ADMIN_PERMS:
            return 400.0
        elif permissions_group == self.PROFESSIONAL_USER_PERMS:
            return 500.0
        elif permissions_group == self.PROFESSIONAL_ADMIN_PERMS:
            return 600.0
        elif permissions_group == self.ENTERPRISE_USER_PERMS:
            return 700.0
        elif permissions_group == self.ENTERPRISE_ADMIN_PERMS:
            return 800.0
        elif permissions_group == self.APP_ADMIN_PERMS:
            return 1000.0
        return -1.0

    @staticmethod
    def add_permissions_group(app_user, permissions_group_name):
        """
        Add the user to the role/group with the given name.
        Args:
            app_user(tethysext.atcore.models.AppUser): AppUser object
            permissions_group_name(str): Name of group to add
        """
        from django.contrib.auth.models import Group

        # Do nothing for staff users
        if app_user.is_staff():
            return

        # Find the group and add the user to it
        group = Group.objects.get(name=permissions_group_name)
        group.user_set.add(app_user.django_user)

    @staticmethod
    def remove_permissions_group(app_user, permissions_group_name):
        """
        Remove the user from the role/group with the given name.
        Args:
            app_user(tethysext.atcore.models.AppUser): AppUser object
            permissions_group_name(str): Name of group to remove
        """
        from django.contrib.auth.models import Group

        # Do nothing for staff users
        if app_user.is_staff():
            return

        # Find the group and remove the user
        group = Group.objects.get(name=permissions_group_name)
        group.user_set.remove(app_user.django_user)

    def remove_all_permissions_groups(self, app_user):
        """
        Remove the user from all permission groups of the bound app.
        Args:
            app_user(tethysext.atcore.models.AppUser): AppUser object
        """
        from django.contrib.auth.models import Group

        # Do nothing for staff users
        if app_user.is_staff():
            return

        django_user = app_user.django_user
        namespace = self.app_namespace + ':'
        groups = Group.objects.filter(name__icontains=namespace)
        for group in groups:
            group.user_set.remove(django_user)

        django_user.save()

    def get_all_permissions_groups_for(self, app_user, as_display_name=False):
        """
        Get all of the custom_permissions groups to which the given user is assigned.
        Args:
            app_user(tethysext.atcore.models.AppUser): AppUser object
            as_display_name(bool): Returns display names instead of programmatic name if True.

        Returns:
            list: all custom_permissions group objects of the bound app to which the user belongs.
        """
        namespace = self.app_namespace + ':'
        if app_user.is_staff():
            from django.contrib.auth.models import Group
            permissions_groups = Group.objects.\
                filter(name__icontains=namespace).\
                values_list('name', flat=True).\
                order_by('-name')
        else:
            permissions_groups = app_user.django_user.groups.\
                filter(name__icontains=namespace).\
                values_list('name', flat=True).\
                order_by('-name')

        groups = []

        for permissions_group in permissions_groups:
            groups.append(self.get_display_name_for(permissions_group) if as_display_name else permissions_group)

        return groups

    def assign_user_permission(self, app_user, role, license=None, **kwargs):
        """
        Add custom_permissions based on combo of role, license and other given criteria.

        Args:
            app_user(tethysext.atcore.models.AppUser): AppUser object
            role(str): Role of user.
            license(str): License of organization to which user belongs.
        """
        # Do nothing for staff users
        if app_user.is_staff() or role == self.ROLES.DEVELOPER:
            return

        # Get appropriate permission group and assign to django user.
        permission_group = self.get_permissions_group_for(role, license)
        django_user = app_user.django_user
        self.add_permissions_group(app_user, permission_group)
        django_user.save()

    def remove_user_permission(self, app_user, role, license=None, **kwargs):
        """
        Remove custom_permissions based on combo of role, license and other given criteria.

        Args:
            app_user(tethysext.atcore.models.AppUser): AppUser object
            role(str): Role of user.
            license(str): License of organization to which user belongs.
        """
        # Don't do anything for users with developer roles.
        if app_user.is_staff() or role == self.ROLES.DEVELOPER:
            return

        # Get appropriate permission group and assign to django user.
        permission_group = self.get_permissions_group_for(role, license)
        django_user = app_user.django_user
        self.remove_permissions_group(app_user, permission_group)
        django_user.save()
