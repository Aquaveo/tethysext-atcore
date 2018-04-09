"""
********************************************************************************
* Name: licenses
* Author: nswain
* Created On: April 04, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


class Licenses:
    """
    Container and methods for licenses.
    """
    STANDARD = 'standard'
    ADVANCED = 'advanced'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'
    NONE = 'no-license'

    def __contains__(self, item):
        return item in self.list()

    def list(self):
        """
        Get a list of all licenses.
        Returns:
            tuple: All available licenses.
        """
        all_licenses = (
            self.STANDARD,
            self.ADVANCED,
            self.PROFESSIONAL,
            self.ENTERPRISE
        )
        return all_licenses

    def is_valid(self, license):
        """
        Validate the given license.
        Args:
            license(str): valid license.
        Returns:
            bool: True if valid, else False.
        """
        return license in self

    def get_rank_for(self, license):
        """
        Get the rank for the given license.
        Args:
            license(str): valid license.

        Returns:
            int: rank value.
        """
        if not self.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        if license == self.STANDARD:
            return 100
        elif license == self.ADVANCED:
            return 200
        elif license == self.PROFESSIONAL:
            return 300
        elif license == self.ENTERPRISE:
            return 400

    def get_display_name_for(self, license):
        """
        Get the display name for the given license.
        Args:
            license(str): valid license.

        Returns:
            str: display name for license.
        """
        if not self.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        if license == self.STANDARD:
            return 'Standard'
        elif license == self.ADVANCED:
            return 'Advanced'
        elif license == self.PROFESSIONAL:
            return 'Professional'
        elif license == self.ENTERPRISE:
            return 'Enterprise'

    def get_assign_permission_for(self, license):
        """
        Get the name of the permission to check for assign rights of the given license.
        Args:
            license(str): valid license.

        Returns:
            str: name of create permission for the given license.
        """
        if not self.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        # TODO: IMPLEMENT THESE PERMISSIONS AND REFACTOR ACCORDINGLY
        if license == self.STANDARD:
            return 'assign_standard_license'
        elif license == self.ADVANCED:
            return 'assign_advanced_license'
        elif license == self.PROFESSIONAL:
            return 'assign_professional_license'
        elif license == self.ENTERPRISE:
            return 'assign_enterprise_license'

    def compare(self, left_license, right_license):
        """
        Compare the rank of two licenses.
        Args:
            left_license(str): valid license.
            right_license(str): valid license.

        Returns:
            str: the winning license.
        """
        if not self.is_valid(left_license):
            raise ValueError('Invalid license given: {}.'.format(left_license))

        if not self.is_valid(right_license):
            raise ValueError('Invalid license given: {}.'.format(right_license))

        if self.get_rank_for(left_license) >= self.get_rank_for(right_license):
            return left_license

        return right_license

    def can_have_clients(self, license):
        """
        License based test to determine if an organization is allowed to have clients.
        Args:
            license: valid license.

        Returns:
            bool: True if organization with this license can have clients, else False.
        """
        if not self.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        if license == self.STANDARD:
            return False
        elif license == self.ADVANCED:
            return False
        elif license == self.PROFESSIONAL:
            return False
        elif license == self.ENTERPRISE:
            return True

    def can_have_consultant(self, license):
        """
        License based test to determine if an organization is allowed to be assigned a consultant.
        Args:
            license: valid license.

        Returns:
            bool: True if organization with this license is allowed to be assigned a consultant, else False.
        """
        if not self.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        if license == self.STANDARD:
            return True
        elif license == self.ADVANCED:
            return True
        elif license == self.PROFESSIONAL:
            return True
        elif license == self.ENTERPRISE:
            return False

    def must_have_consultant(self, license):
        """
        License based test to determine if an organization must be assigned a consultant.
        Args:
            license: valid license.

        Returns:
            bool: True if organization with this license must be assigned a constultant, else False
        """
        if not self.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        if license == self.STANDARD:
            return False
        elif license == self.ADVANCED:
            return False
        elif license == self.PROFESSIONAL:
            return False
        elif license == self.ENTERPRISE:
            return False
