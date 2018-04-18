from tethys_sdk.permissions import Permission, PermissionGroup


class PermissionsGenerator:

    def __init__(self, permission_manager):
        """
        Used to generate permissions groups associated with the app_users extension.
        Args:
            permission_manager(AppPermissionManager): a permission manager instance bound to the app.
        """
        self.permission_manager = permission_manager

        self.custom_permissions = {}
        for permission_group in self.permission_manager.list():
            self.custom_permissions[permission_group] = []

    def add_permissions_for(self, permission_group, permissions):
        """
        Add a list of permissions to the specified permission group.
        Args:
            permission_group(str): name of a permission group.
            permissions(list<Permission>): list of Permission instances.
        """
        if permission_group not in self.custom_permissions:
            raise ValueError("Invalid permission group: {}".format(permission_group))

        if not isinstance(permissions, list):
            raise ValueError("Argument custom_permissions must be a list: {}".format(permission_group))

        self.custom_permissions[permission_group].extend(permissions)

    def generate(self):
        """
        Generate list of permission groups.
        Returns:
            list<PermissionGroups>: all permission groups with permissions.
        """

        # Resource Management Permissions
        view_all_resources = Permission(
            name='view_all_resources',
            description='View all resources'
        )

        view_resources = Permission(
            name='view_resources',
            description='View resources'
        )

        view_resource_details = Permission(
            name='view_resource_details',
            description='View details for resources'
        )

        create_resource = Permission(
            name='create_resource',
            description='Create resources'
        )

        edit_resource = Permission(
            name='edit_resource',
            description='Edit resources'
        )

        delete_resource = Permission(
            name='delete_resource',
            description='Delete resources'
        )

        always_delete_resource = Permission(
            name='always_delete_resource',
            description='Delete resource even if not editable'
        )

        # User management custom_permissions
        modify_user_manager = Permission(
            name='modify_user_manager',
            description='Modify the manager of a user'
        )

        modify_users = Permission(
            name='modify_users',
            description='Edit, delete, and create app users'
        )

        view_users = Permission(
            name='view_users',
            description='View app users'
        )

        view_all_users = Permission(
            name='view_all_users',
            description='View all users'
        )

        assign_org_users_role = Permission(
            name='assign_org_users_role',
            description='Assign organization user role'
        )

        assign_org_admin_role = Permission(
            name='assign_org_admin_role',
            description='Assign organization admin role'
        )

        assign_app_admin_role = Permission(
            name='assign_app_admin_role',
            description='Assign app admin role'
        )

        assign_developer_role = Permission(
            name='assign_developer_role',
            description='Assign developer role'
        )

        # Organization custom_permissions
        view_all_organizations = Permission(
            name='view_all_organizations',
            description='View any organization'
        )

        modify_organizations = Permission(
            name='modify_organizations',
            description='Edit, delete, and create organizations'
        )

        modify_organization_members = Permission(
            name='modify_organization_members',
            description='Assign and remove members from organizations'
        )

        view_organizations = Permission(
            name='view_organizations',
            description='View organizations'
        )

        # Assignment custom_permissions
        assign_any_resource = Permission(
            name='assign_any_resource',
            description='Assign any resource to organizations'
        )

        assign_any_user = Permission(
            name='assign_any_user',
            description='Assign any user to organizations'
        )

        assign_any_organization = Permission(
            name='assign_any_organization',
            description='Assign any organization to resources'
        )

        # Role identifier custom_permissions
        has_standard_user_role = Permission(
            name='has_standard_user_role',
            description='Has Standard Viewer role'
        )

        has_standard_admin_role = Permission(
            name='has_standard_admin_role',
            description='Has Standard Admin role'
        )

        has_advanced_user_role = Permission(
            name='has_advanced_user_role',
            description='Has Advanced Viewer role'
        )

        has_advanced_admin_role = Permission(
            name='has_advanced_admin_role',
            description='Has Advanced Admin role'
        )

        has_professional_user_role = Permission(
            name='has_professional_user_role',
            description='Has Professional Viewer role'
        )

        has_professional_admin_role = Permission(
            name='has_professional_admin_role',
            description='Has Professional Admin role'
        )

        has_enterprise_user_role = Permission(
            name='has_enterprise_user_role',
            description='Has Enterprise Viewer role'
        )

        has_enterprise_admin_role = Permission(
            name='has_enterprise_admin_role',
            description='Has Enterprise Admin role'
        )

        has_app_admin_role = Permission(
            name='has_app_admin_role',
            description='Has app admin role'
        )

        assign_standard_license = Permission(
            name='assign_standard_license',
            description='Assign standard license'
        )

        assign_advanced_license = Permission(
            name='assign_advanced_license',
            description='Assign advanced license'
        )

        assign_professional_license = Permission(
            name='assign_professional_license',
            description='Assign professional license'
        )

        assign_enterprise_license = Permission(
            name='assign_enterprise_license',
            description='Assign enterprise license'
        )

        # Standard Viewer
        standard_user_perms = [
            view_resource_details,
            view_organizations,
            view_resources
        ]

        standard_user_role = PermissionGroup(
            name=self.permission_manager.STD_U_PERMS,
            permissions=standard_user_perms + [has_standard_user_role] +
                        self.custom_permissions[self.permission_manager.STD_U_PERMS]  # noqa: E131
        )

        # Standard Admin
        standard_admin_perms = standard_user_perms + [
            create_resource, edit_resource, delete_resource,
            view_users, modify_users, modify_organization_members,
            assign_org_users_role
        ]

        standard_admin_role = PermissionGroup(
            name=self.permission_manager.STD_A_PERMS,
            permissions=standard_admin_perms + [has_standard_admin_role] +
                        self.custom_permissions[self.permission_manager.STD_A_PERMS]  # noqa: E131
        )

        # Advanced Viewer
        advanced_user_perms = standard_user_perms

        advanced_user_role = PermissionGroup(
            name=self.permission_manager.ADV_U_PERMS,
            permissions=advanced_user_perms + [has_advanced_user_role] +
                        self.custom_permissions[self.permission_manager.ADV_U_PERMS]  # noqa: E131
        )

        # Advanced Admin
        advanced_admin_perms = standard_admin_perms + advanced_user_perms

        advanced_admin_role = PermissionGroup(
            name=self.permission_manager.ADV_A_PERMS,
            permissions=advanced_admin_perms + [has_advanced_admin_role] +
                        self.custom_permissions[self.permission_manager.ADV_A_PERMS]  # noqa: E131
        )

        # Professional Viewer
        professional_user_perms = advanced_user_perms

        professional_user_role = PermissionGroup(
            name=self.permission_manager.PRO_U_PERMS,
            permissions=professional_user_perms + [has_professional_user_role] +
                        self.custom_permissions[self.permission_manager.PRO_U_PERMS]  # noqa: E131
        )

        # Professional Admin
        professional_admin_perms = advanced_admin_perms + professional_user_perms

        professional_admin_role = PermissionGroup(
            name=self.permission_manager.PRO_A_PERMS,
            permissions=professional_admin_perms + [has_professional_admin_role] +
                        self.custom_permissions[self.permission_manager.PRO_A_PERMS]  # noqa: E131
        )

        # Enterprise Viewer
        enterprise_user_perms = professional_user_perms

        enterprise_user_role = PermissionGroup(
            name=self.permission_manager.ENT_U_PERMS,
            permissions=enterprise_user_perms + [has_enterprise_user_role] +
                        self.custom_permissions[self.permission_manager.ENT_U_PERMS]  # noqa: E131
        )

        # Enterprise Admin
        enterprise_admin_perms = professional_admin_perms + enterprise_user_perms + [
            modify_organizations, assign_advanced_license,
            assign_standard_license, assign_professional_license
        ]

        enterprise_admin_role = PermissionGroup(
            name=self.permission_manager.ENT_A_PERMS,
            permissions=enterprise_admin_perms + [has_enterprise_admin_role] +
                        self.custom_permissions[self.permission_manager.ENT_A_PERMS]  # noqa: E131
        )

        # App admin role
        app_admin_perms = [
            view_resource_details,
            view_all_resources, create_resource, edit_resource, delete_resource, always_delete_resource,
            modify_user_manager, modify_users, view_users, view_all_users, assign_org_users_role,
            assign_org_admin_role, assign_app_admin_role, assign_developer_role, view_organizations,
            view_all_organizations, modify_organizations, modify_organization_members,
            assign_any_resource, assign_any_organization, assign_any_user, assign_advanced_license,
            assign_standard_license, assign_professional_license, assign_enterprise_license
        ]

        app_admin_role = PermissionGroup(
            name=self.permission_manager.APP_A_PERMS,
            permissions=app_admin_perms + [has_app_admin_role] +
                        self.custom_permissions[self.permission_manager.APP_A_PERMS]  # noqa: E131
        )

        permissions = [
            standard_user_role, standard_admin_role,
            advanced_user_role, advanced_admin_role,
            professional_user_role, professional_admin_role,
            enterprise_user_role, enterprise_admin_role, app_admin_role
        ]

        return permissions
