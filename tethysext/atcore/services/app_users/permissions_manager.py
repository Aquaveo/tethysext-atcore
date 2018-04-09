"""
********************************************************************************
* Name: permissions_manager.py
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""



class AppPermissionsManager:

    _STD_V_ROLE = 'standard_viewer_role'
    _STD_A_ROLE = 'standard_admin_role'
    _ADV_V_ROLE = 'advanced_viewer_role'
    _ADV_A_ROLE = 'advanced_admin_role'
    _PRO_V_ROLE = 'professional_viewer_role'
    _PRO_A_ROLE = 'professional_admin_role'
    _ENT_V_ROLE = 'enterprise_viewer_role'
    _ENT_A_ROLE = 'enterprise_admin_role'
    _APP_A_ROLE = 'app_admin_role'

    def __init__(self, app_namespace, roles, licenses):
        """
        Manages permissions for a given app.
        Args:
            app_namespace(str): Namespace of the app (e.g.: "epanet").
            roles (atcore.services.app_users.Roles): Valid roles instance.
            licenses: (atcore.services.app_users.Licenses): Valid licenses instance.
        """
        self.app_namespace = app_namespace
        self.ROLES = roles
        self.LICENSES = licenses

        self.STANDARD_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self._STD_V_ROLE)
        self.STANDARD_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self._STD_A_ROLE)
        self.ADVANCED_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self._ADV_V_ROLE)
        self.ADVANCED_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self._ADV_A_ROLE)
        self.PROFESSIONAL_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self._PRO_V_ROLE)
        self.PROFESSIONAL_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self._PRO_A_ROLE)
        self.ENTERPRISE_VIEWER_ROLE = '{}:{}'.format(self.app_namespace, self._ENT_V_ROLE)
        self.ENTERPRISE_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self._ENT_A_ROLE)
        self.APP_ADMIN_ROLE = '{}:{}'.format(self.app_namespace, self._APP_A_ROLE)

    def get_display_name_for(self, permissions_group):
        """
        Get the display name for the given permission group.
        Args:
            permissions_group(django.contrib.auth.models.Group): permission group.

        Returns:
            str: Display name for the given permissions group.
        """
        # TODO: Implement this...
        raise NotImplementedError()

    def get_permissions_group_for(self, role, license=None, **kwargs):
        """
        Get the name of the permissions group for the given role, license, and other criteria.
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

    @staticmethod
    def add_permissions_group(django_user, permissions_group_name):
        """
        Add the user to the role/group with the given name.
        Args:
            django_user(django.contrib.auth.models.User): Django User object
            permissions_group_name(str): Name of group to add
        """
        from django.contrib.auth.models import Group
        group = Group.objects.get(name=permissions_group_name)
        group.user_set.add(django_user)

    @staticmethod
    def remove_permissions_group(django_user, permissions_group_name):
        """
        Remove the user from the role/group with the given name.
        Args:
            django_user(django.contrib.auth.models.User): Django User object
            permissions_group_name(str): Name of group to remove
        """
        from django.contrib.auth.models import Group
        group = Group.objects.get(name=permissions_group_name)
        group.user_set.remove(django_user)

    def remove_all_permissions_groups(self, django_user):
        """
        Remove the user from all permission groups of the bound app.
        Args:
            django_user(django.contrib.auth.models.User):  Django User object
        """
        from django.contrib.auth.models import Group
        namespace = self.app_namespace + ':'
        groups = Group.objects.filter(name__icontains=namespace)
        for group in groups:
            group.user_set.remove(django_user)

    def get_all_permissions_groups_for(self, django_user, as_display_name=False):
        """
        Get all of the permissions groups to which the given user is assigned.
        Args:
            django_user(django.contrib.auth.models.User): Django User object.
            as_display_name(bool): Returns display names instead of programmatic name if True.

        Returns:
            list: all permissions group objects of the bound app to which the user belongs.
        """
        namespace = self.app_namespace + ':'
        if django_user.is_staff:
            from django.contrib.auth.models import Group
            permissions_groups = Group.objects.\
                filter(name__icontains=namespace).\
                values_list('name', flat=True).\
                order_by('-name')
        else:
            permissions_groups = django_user.groups.\
                filter(name__icontains=namespace).\
                values_list('name', flat=True).\
                order_by('-name')

        groups = []

        for permissions_group in permissions_groups:
            groups.append(self.get_display_name_for(permissions_group) if as_display_name else permissions_group)

        return groups

    def assign_user_permission(self, django_user, role, license, **kwargs):
        """
        Add permissions based on combo of role, license and other given criteria.

        Args:
            django_user(django.contrib.auth.models.User): Django Request or User object.
            role(str): Role of user.
            license(str): License of organization to which user belongs.
        """
        # Don't do anything for users with developer roles.
        if role == self.ROLES.DEVELOPER:
            return

        # Get appropriate permission group and assign to django user.
        permission_group = self.get_permissions_group_for(role, license)
        self.add_permissions_group(django_user, permission_group)
        django_user.save()

    def remove_user_permission(self, django_user, role, license=None, **kwargs):
        """
        Remove permissions based on combo of role, license and other given criteria.

        Args:
            django_user(django.contrib.auth.models.User): Django Request or User object.
            role(str): Role of user.
            license(str): License of organization to which user belongs.
        """
        # Don't do anything for users with developer roles.
        if role == self.ROLES.DEVELOPER:
            return

        # Get appropriate permission group and assign to django user.
        permission_group = self.get_permissions_group_for(role, license)
        self.remove_permissions_group(django_user, permission_group)
        django_user.save()
