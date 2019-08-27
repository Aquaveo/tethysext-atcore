"""
********************************************************************************
* Name: user_roles.py
* Author: nswain
* Created On: April 2, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


class Roles:
    """
    Container and methods for user roles.
    """
    ORG_USER = 'user_role_org_user'
    ORG_REVIEWER = 'user_role_org_reviewer'
    ORG_ADMIN = 'user_role_org_admin'
    APP_ADMIN = 'user_role_app_admin'
    DEVELOPER = 'user_role_developer'

    def __contains__(self, item):
        return item in self.list()

    def list(self):
        """
        Get a list of all roles.
        Returns:
            tuple: All available roles.
        """
        all_roles = (self.ORG_USER, self.ORG_REVIEWER, self.ORG_ADMIN, self.APP_ADMIN, self.DEVELOPER)
        return all_roles

    def is_valid(self, role):
        """
        Validate the given role.
        Args:
            role(str): valid role.
        Returns:
            bool: True if valid, else False.
        """
        return role in self

    def get_rank_for(self, role):
        """
        Get the rank for the given role.
        Args:
            role(str): valid role.

        Returns:
            int: rank value.
        """
        if not self.is_valid(role):
            raise ValueError('Invalid role given: {}.'.format(role))

        if role == self.ORG_USER:
            return 100
        elif role == self.ORG_REVIEWER:
            return 200
        elif role == self.ORG_ADMIN:
            return 300
        elif role == self.APP_ADMIN:
            return 1000
        elif role == self.DEVELOPER:
            # THIS SHOULD OUT-RANK ALL ROLES.
            return float('inf')

    def get_display_name_for(self, role):
        """
        Get the display name for the given role.
        Args:
            role(str): valid role.

        Returns:
            str: display name for role.
        """
        if not self.is_valid(role):
            raise ValueError('Invalid role given: {}.'.format(role))

        if role == self.ORG_USER:
            return 'Organization User'
        elif role == self.ORG_REVIEWER:
            return 'Organization Reviewer'
        elif role == self.ORG_ADMIN:
            return 'Organization Admin'
        elif role == self.APP_ADMIN:
            return 'App Admin'
        elif role == self.DEVELOPER:
            # THIS SHOULD OUT-RANK ALL ROLES.
            return 'Developer'

    def get_assign_permission_for(self, role):
        """
        Get the name of the permission to check for assign rights of the given role.
        Args:
            role(str): valid role.

        Returns:
            str: name of create permission for the given role.
        """
        if not self.is_valid(role):
            raise ValueError('Invalid role given: {}.'.format(role))

        if role == self.ORG_USER:
            return 'assign_org_user_role'
        if role == self.ORG_REVIEWER:
            return 'assign_org_reviewer_role'
        elif role == self.ORG_ADMIN:
            return 'assign_org_admin_role'
        elif role == self.APP_ADMIN:
            return 'assign_app_admin_role'
        elif role == self.DEVELOPER:
            return 'assign_developer_role'

    def compare(self, left_role, right_role):
        """
        Compare the rank of two roles.
        Args:
            left_role(str): valid role.
            right_role(str): valid role.

        Returns:
            str: the winning role.
        """
        if not self.is_valid(left_role):
            raise ValueError('Invalid role given: {}.'.format(left_role))

        if not self.is_valid(right_role):
            raise ValueError('Invalid role given: {}.'.format(right_role))

        if self.get_rank_for(left_role) >= self.get_rank_for(right_role):
            return left_role

        return right_role

    def get_organization_required_roles(self):
        """
        Users with these roles must be assigned to an organization.
        Returns:
            list: organization roles.
        """
        return [self.ORG_USER, self.ORG_REVIEWER, self.ORG_ADMIN]

    def get_no_organization_roles(self):
        """
        Users with these roles cannot be assigned to an organization.
        Returns:
            list: organization roles.
        """
        return [self.APP_ADMIN, self.DEVELOPER]
