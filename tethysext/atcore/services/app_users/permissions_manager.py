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
    ROLES = Roles()
    LICENSES = Licenses()

    # Standard License Permissions Groups
    STD_U_PERMS = 'standard_user_perms'
    STD_R_PERMS = 'standard_reviewer_perms'
    STD_A_PERMS = 'standard_admin_perms'

    # Advanced License Permissions Groups
    ADV_U_PERMS = 'advanced_user_perms'
    ADV_R_PERMS = 'advanced_reviewer_perms'
    ADV_A_PERMS = 'advanced_admin_perms'

    # Professional License Permissions Groups
    PRO_U_PERMS = 'professional_user_perms'
    PRO_R_PERMS = 'professional_reviewer_perms'
    PRO_A_PERMS = 'professional_admin_perms'

    # Enterprise License Permissions Groups
    ENT_U_PERMS = 'enterprise_user_perms'
    ENT_R_PERMS = 'enterprise_reviewer_perms'
    ENT_A_PERMS = 'enterprise_admin_perms'

    # Global Permissions Groups
    APP_A_PERMS = 'app_admin_perms'

    PERMISSIONS_GROUP_MAP = {
        LICENSES.STANDARD: {
            ROLES.ORG_USER: STD_U_PERMS,
            ROLES.ORG_REVIEWER: STD_R_PERMS,
            ROLES.ORG_ADMIN: STD_A_PERMS,
        },
        LICENSES.ADVANCED: {
            ROLES.ORG_USER: ADV_U_PERMS,
            ROLES.ORG_REVIEWER: ADV_R_PERMS,
            ROLES.ORG_ADMIN: ADV_A_PERMS,
        },
        LICENSES.PROFESSIONAL: {
            ROLES.ORG_USER: PRO_U_PERMS,
            ROLES.ORG_REVIEWER: PRO_R_PERMS,
            ROLES.ORG_ADMIN: PRO_A_PERMS,
        },
        LICENSES.ENTERPRISE: {
            ROLES.ORG_USER: ENT_U_PERMS,
            ROLES.ORG_REVIEWER: ENT_R_PERMS,
            ROLES.ORG_ADMIN: ENT_A_PERMS,
        }
    }

    def __init__(self, app_namespace):
        """
        Manages custom_permissions for a given app.
        Args:
            app_namespace(str): Namespace of the app (e.g.: "my_first_app").
        """
        self.app_namespace = app_namespace

        # Namespaced Standard License Permissions Groups
        self.STANDARD_USER_PERMS = '{}:{}'.format(self.app_namespace, self.STD_U_PERMS)
        self.STANDARD_REVIEWER_PERMS = '{}:{}'.format(self.app_namespace, self.STD_R_PERMS)
        self.STANDARD_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self.STD_A_PERMS)

        # Namespaced Advanced License Permissions Groups
        self.ADVANCED_USER_PERMS = '{}:{}'.format(self.app_namespace, self.ADV_U_PERMS)
        self.ADVANCED_REVIEWER_PERMS = '{}:{}'.format(self.app_namespace, self.ADV_R_PERMS)
        self.ADVANCED_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self.ADV_A_PERMS)

        # Namespaced Professional License Permissions Groups
        self.PROFESSIONAL_USER_PERMS = '{}:{}'.format(self.app_namespace, self.PRO_U_PERMS)
        self.PROFESSIONAL_REVIEWER_PERMS = '{}:{}'.format(self.app_namespace, self.PRO_R_PERMS)
        self.PROFESSIONAL_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self.PRO_A_PERMS)

        # Namespaced Enterprise License Permissions Groups
        self.ENTERPRISE_USER_PERMS = '{}:{}'.format(self.app_namespace, self.ENT_U_PERMS)
        self.ENTERPRISE_REVIEWER_PERMS = '{}:{}'.format(self.app_namespace, self.ENT_R_PERMS)
        self.ENTERPRISE_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self.ENT_A_PERMS)

        # Namespaced Global Permissions Groups
        self.APP_ADMIN_PERMS = '{}:{}'.format(self.app_namespace, self.APP_A_PERMS)

        self.NAMESPACED_PERMISSIONS_GROUP_MAP = {
            self.LICENSES.STANDARD: {
                self.ROLES.ORG_USER: self.STANDARD_USER_PERMS,
                self.ROLES.ORG_REVIEWER: self.STANDARD_REVIEWER_PERMS,
                self.ROLES.ORG_ADMIN: self.STANDARD_ADMIN_PERMS,
            },
            self.LICENSES.ADVANCED: {
                self.ROLES.ORG_USER: self.ADVANCED_USER_PERMS,
                self.ROLES.ORG_REVIEWER: self.ADVANCED_REVIEWER_PERMS,
                self.ROLES.ORG_ADMIN: self.ADVANCED_ADMIN_PERMS,
            },
            self.LICENSES.PROFESSIONAL: {
                self.ROLES.ORG_USER: self.PROFESSIONAL_USER_PERMS,
                self.ROLES.ORG_REVIEWER: self.PROFESSIONAL_REVIEWER_PERMS,
                self.ROLES.ORG_ADMIN: self.PROFESSIONAL_ADMIN_PERMS,
            },
            self.LICENSES.ENTERPRISE: {
                self.ROLES.ORG_USER: self.ENTERPRISE_USER_PERMS,
                self.ROLES.ORG_REVIEWER: self.ENTERPRISE_REVIEWER_PERMS,
                self.ROLES.ORG_ADMIN: self.ENTERPRISE_ADMIN_PERMS,
            }
        }

    def list(self, with_namespace=False):
        """
        List all permission groups.
        Returns:
            list<str>: names of all the custom_permissions groups.
        """
        enabled_licenses = self.LICENSES.list()
        enabled_roles = self.ROLES.list()
        permissions_groups = []

        if with_namespace:
            permissions_group_map = self.NAMESPACED_PERMISSIONS_GROUP_MAP
            app_admin_group = self.APP_ADMIN_PERMS
        else:
            permissions_group_map = self.PERMISSIONS_GROUP_MAP
            app_admin_group = self.APP_A_PERMS

        for enabled_license in enabled_licenses:
            for enabled_role in enabled_roles:
                # Skip non-organizational roles
                if enabled_role in self.ROLES.get_no_organization_roles():
                    continue
                permissions_groups.append(permissions_group_map[enabled_license][enabled_role])

        if self.ROLES.APP_ADMIN in enabled_roles:
            permissions_groups.append(app_admin_group)

        return permissions_groups

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

        elif role == self.ROLES.ORG_REVIEWER:
            if license == self.LICENSES.STANDARD:
                return self.STANDARD_REVIEWER_PERMS
            elif license == self.LICENSES.ADVANCED:
                return self.STANDARD_REVIEWER_PERMS
            elif license == self.LICENSES.PROFESSIONAL:
                return self.PROFESSIONAL_REVIEWER_PERMS
            elif license == self.LICENSES.ENTERPRISE:
                return self.ENTERPRISE_REVIEWER_PERMS

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
        display_name_map = {
            self.STANDARD_USER_PERMS: 'Standard User',
            self.STANDARD_REVIEWER_PERMS: 'Standard Reviewer',
            self.STANDARD_ADMIN_PERMS: 'Standard Admin',

            self.ADVANCED_USER_PERMS: 'Advanced User',
            self.ADVANCED_REVIEWER_PERMS: 'Advanced Reviewer',
            self.ADVANCED_ADMIN_PERMS: 'Advanced Admin',

            self.PROFESSIONAL_USER_PERMS: 'Professional User',
            self.PROFESSIONAL_REVIEWER_PERMS: 'Professional Reviewer',
            self.PROFESSIONAL_ADMIN_PERMS: 'Professional Admin',

            self.ENTERPRISE_USER_PERMS: 'Enterprise User',
            self.ENTERPRISE_REVIEWER_PERMS: 'Enterprise Reviewer',
            self.ENTERPRISE_ADMIN_PERMS: 'Enterprise Admin',

            self.APP_ADMIN_PERMS: 'App Admin',
        }

        if permissions_group in display_name_map:
            return display_name_map[permissions_group]

        return ''

    def get_has_role_permission_for(self, role, license=None):
        """
        Get name of the permission that can be tested to see if a user has the given role.
        Args:
            role(str): Role of user.
            license(str): License of organization to which user belongs (optional).

        Returns:
            str: name of the "has role" permission.
        """
        has_role_permission = None

        if role == self.ROLES.ORG_USER:
            if license is not None:
                if license == self.LICENSES.STANDARD:
                    has_role_permission = 'has_standard_user_role'
                elif license == self.LICENSES.ADVANCED:
                    has_role_permission = 'has_advanced_user_role'
                elif license == self.LICENSES.PROFESSIONAL:
                    has_role_permission = 'has_professional_user_role'
                elif license == self.LICENSES.ENTERPRISE:
                    has_role_permission = 'has_enterprise_user_role'
            else:
                has_role_permission = 'has_org_user_role'

        if role == self.ROLES.ORG_REVIEWER:
            if license is not None:
                if license == self.LICENSES.STANDARD:
                    has_role_permission = 'has_standard_reviewer_role'
                elif license == self.LICENSES.ADVANCED:
                    has_role_permission = 'has_advanced_reviewer_role'
                elif license == self.LICENSES.PROFESSIONAL:
                    has_role_permission = 'has_professional_reviewer_role'
                elif license == self.LICENSES.ENTERPRISE:
                    has_role_permission = 'has_enterprise_reviewer_role'
            else:
                has_role_permission = 'has_org_reviewer_role'

        if role == self.ROLES.ORG_ADMIN:
            if license is not None:
                if license == self.LICENSES.STANDARD:
                    has_role_permission = 'has_standard_admin_role'
                elif license == self.LICENSES.ADVANCED:
                    has_role_permission = 'has_advanced_admin_role'
                elif license == self.LICENSES.PROFESSIONAL:
                    has_role_permission = 'has_professional_admin_role'
                elif license == self.LICENSES.ENTERPRISE:
                    has_role_permission = 'has_enterprise_admin_role'
            else:
                has_role_permission = 'has_org_admin_role'

        if role == self.ROLES.APP_ADMIN:
            has_role_permission = 'has_app_admin_role'

        return has_role_permission

    def get_rank_for(self, permissions_group):
        """
        Get the rank for the given permission group.
        Args:
            permissions_group(str): name of permission group.

        Returns:
            int: Rank for given permission group.
        """
        rank_map = {
            self.STANDARD_USER_PERMS: 1100.0,
            self.STANDARD_REVIEWER_PERMS: 1200.0,
            self.STANDARD_ADMIN_PERMS: 1300.0,

            self.ADVANCED_USER_PERMS: 2100.0,
            self.ADVANCED_REVIEWER_PERMS: 2200.0,
            self.ADVANCED_ADMIN_PERMS: 2300.0,

            self.PROFESSIONAL_USER_PERMS: 3100.0,
            self.PROFESSIONAL_REVIEWER_PERMS: 3200.0,
            self.PROFESSIONAL_ADMIN_PERMS: 3400.0,

            self.ENTERPRISE_USER_PERMS: 4100.0,
            self.ENTERPRISE_REVIEWER_PERMS: 4200.0,
            self.ENTERPRISE_ADMIN_PERMS: 4300.0,

            self.APP_ADMIN_PERMS: 10000.0,
        }

        if permissions_group in rank_map:
            return rank_map[permissions_group]

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
