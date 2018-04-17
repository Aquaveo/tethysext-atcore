"""
********************************************************************************
* Name: permissions_manager.py
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.services.app_users.user_roles import Roles
from tethysext.atcore.services.app_users.licenses import Licenses


class AppPermissionsManager:
    STD_V_ROLE = 'standard_viewer_role'
    STD_A_ROLE = 'standard_admin_role'
    ADV_V_ROLE = 'advanced_viewer_role'
    ADV_A_ROLE = 'advanced_admin_role'
    PRO_V_ROLE = 'professional_viewer_role'
    PRO_A_ROLE = 'professional_admin_role'
    ENT_V_ROLE = 'enterprise_viewer_role'
    ENT_A_ROLE = 'enterprise_admin_role'
    APP_A_ROLE = 'app_admin_role'

    ROLES = Roles()
    LICENSES = Licenses()

    def __init__(self, app_namespace):
        """
        Manages custom_permissions for a given app.
        Args:
            app_namespace(str): Namespace of the app (e.g.: "epanet").
        """
        self.app_namespace = app_namespace

        self.STANDARD_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self.STD_V_ROLE)
        self.STANDARD_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self.STD_A_ROLE)
        self.ADVANCED_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self.ADV_V_ROLE)
        self.ADVANCED_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self.ADV_A_ROLE)
        self.PROFESSIONAL_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self.PRO_V_ROLE)
        self.PROFESSIONAL_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self.PRO_A_ROLE)
        self.ENTERPRISE_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self.ENT_V_ROLE)
        self.ENTERPRISE_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self.ENT_A_ROLE)
        self.APP_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self.APP_A_ROLE)

    def list(self, with_namespace=False):
        """
        List all permission groups.
        Returns:
            list<str>: names of all the custom_permissions groups.
        """
        if with_namespace:
            return [
                self.STANDARD_VIEWER_ROLE,
                self.STANDARD_ADMIN_ROLE,
                self.ADVANCED_VIEWER_ROLE,
                self.ADVANCED_ADMIN_ROLE,
                self.PROFESSIONAL_VIEWER_ROLE,
                self.PROFESSIONAL_ADMIN_ROLE,
                self.ENTERPRISE_VIEWER_ROLE,
                self.ENTERPRISE_ADMIN_ROLE,
                self.APP_ADMIN_ROLE
            ]
        else:
            return [
                self.STD_V_ROLE,
                self.STD_A_ROLE,
                self.ADV_V_ROLE,
                self.ADV_A_ROLE,
                self.PRO_V_ROLE,
                self.PRO_A_ROLE,
                self.ENT_V_ROLE,
                self.ENT_A_ROLE,
                self.APP_A_ROLE
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
                return self.STANDARD_VIEWER_ROLE
            elif license == self.LICENSES.ADVANCED:
                return self.ADVANCED_VIEWER_ROLE
            elif license == self.LICENSES.PROFESSIONAL:
                return self.PROFESSIONAL_VIEWER_ROLE
            elif license == self.LICENSES.ENTERPRISE:
                return self.ENTERPRISE_VIEWER_ROLE

        elif role == self.ROLES.ORG_ADMIN:
            if license == self.LICENSES.STANDARD:
                return self.STANDARD_ADMIN_ROLE
            elif license == self.LICENSES.ADVANCED:
                return self.ADVANCED_ADMIN_ROLE
            elif license == self.LICENSES.PROFESSIONAL:
                return self.PROFESSIONAL_ADMIN_ROLE
            elif license == self.LICENSES.ENTERPRISE:
                return self.ENTERPRISE_ADMIN_ROLE

        elif role == self.ROLES.APP_ADMIN:
            return self.APP_ADMIN_ROLE

    def get_display_name_for(self, permissions_group):
        """
        Get the display name for the given permission group.
        Args:
            permissions_group(django.contrib.auth.models.Group): permission group.

        Returns:
            str: Display name for the given custom_permissions group.
        """
        if permissions_group == self.STANDARD_VIEWER_ROLE:
            return 'Standard Viewer'
        elif permissions_group == self.STANDARD_ADMIN_ROLE:
            return 'Standard Admin'
        elif permissions_group == self.ADVANCED_VIEWER_ROLE:
            return 'Advanced Viewer'
        elif permissions_group == self.ADVANCED_ADMIN_ROLE:
            return 'Advanced Admin'
        elif permissions_group == self.PROFESSIONAL_VIEWER_ROLE:
            return 'Professional Viewer'
        elif permissions_group == self.PROFESSIONAL_ADMIN_ROLE:
            return 'Professional Admin'
        elif permissions_group == self.ENTERPRISE_VIEWER_ROLE:
            return 'Enterprise Viewer'
        elif permissions_group == self.ENTERPRISE_ADMIN_ROLE:
            return 'Enterprise Admin'
        elif permissions_group == self.APP_ADMIN_ROLE:
            return 'App Admin'
        return ''

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

    def assign_user_permission(self, app_user, role, license, **kwargs):
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
            app_user(tethysext.atcore.models.AppUser): AppUser object            role(str): Role of user.
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
