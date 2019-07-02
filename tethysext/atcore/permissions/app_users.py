from tethys_sdk.permissions import Permission, PermissionGroup


class PermissionsGenerator:

    def __init__(self, permission_manager):
        """
        Used to generate permissions groups associated with the app_users extension.
        Args:
            permission_manager(AppPermissionManager): a permission manager instance bound to the app.
        """
        self.permission_manager = permission_manager

        self.permissions_groups = {}
        self.permissions = {}
        self.custom_permissions = {}

        for permission_group in self.permission_manager.list():
            self.custom_permissions[permission_group] = []
            self.permissions[permission_group] = []

        self.all_permissions = []
        self.all_permissions_groups = []

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
            raise ValueError("Argument permissions must be a list: {}".format(permission_group))

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
        self.all_permissions.append(view_all_resources)

        view_resources = Permission(
            name='view_resources',
            description='View resources'
        )
        self.all_permissions.append(view_resources)

        view_resource_details = Permission(
            name='view_resource_details',
            description='View details for resources'
        )
        self.all_permissions.append(view_resource_details)

        create_resource = Permission(
            name='create_resource',
            description='Create resources'
        )
        self.all_permissions.append(create_resource)

        edit_resource = Permission(
            name='edit_resource',
            description='Edit resources'
        )
        self.all_permissions.append(edit_resource)

        delete_resource = Permission(
            name='delete_resource',
            description='Delete resources'
        )
        self.all_permissions.append(delete_resource)

        always_delete_resource = Permission(
            name='always_delete_resource',
            description='Delete resource even if not editable'
        )
        self.all_permissions.append(always_delete_resource)

        # User management permissions
        modify_user_manager = Permission(
            name='modify_user_manager',
            description='Modify the manager of a user'
        )
        self.all_permissions.append(modify_user_manager)

        modify_users = Permission(
            name='modify_users',
            description='Edit, delete, and create app users'
        )
        self.all_permissions.append(modify_users)

        view_users = Permission(
            name='view_users',
            description='View app users'
        )
        self.all_permissions.append(view_users)

        view_all_users = Permission(
            name='view_all_users',
            description='View all users'
        )
        self.all_permissions.append(view_all_users)

        assign_org_users_role = Permission(
            name='assign_org_users_role',
            description='Assign organization user role'
        )
        self.all_permissions.append(assign_org_users_role)

        assign_org_admin_role = Permission(
            name='assign_org_admin_role',
            description='Assign organization admin role'
        )
        self.all_permissions.append(assign_org_admin_role)

        assign_app_admin_role = Permission(
            name='assign_app_admin_role',
            description='Assign app admin role'
        )
        self.all_permissions.append(assign_app_admin_role)

        assign_developer_role = Permission(
            name='assign_developer_role',
            description='Assign developer role'
        )
        self.all_permissions.append(assign_developer_role)

        # Organization permissions
        view_all_organizations = Permission(
            name='view_all_organizations',
            description='View any organization'
        )
        self.all_permissions.append(view_all_organizations)

        create_organizations = Permission(
            name='create_organizations',
            description='Edit, delete, and create organizations'
        )
        self.all_permissions.append(create_organizations)

        edit_organizations = Permission(
            name='edit_organizations',
            description='Edit organizations'
        )
        self.all_permissions.append(edit_organizations)

        delete_organizations = Permission(
            name='delete_organizations',
            description='Delete organizations'
        )
        self.all_permissions.append(delete_organizations)

        modify_organization_members = Permission(
            name='modify_organization_members',
            description='Assign and remove members from organizations'
        )
        self.all_permissions.append(modify_organization_members)

        view_organizations = Permission(
            name='view_organizations',
            description='View organizations'
        )
        self.all_permissions.append(view_organizations)

        # Assignment permissions
        assign_any_resource = Permission(
            name='assign_any_resource',
            description='Assign any resource to organizations'
        )
        self.all_permissions.append(assign_any_resource)

        assign_any_user = Permission(
            name='assign_any_user',
            description='Assign any user to organizations'
        )
        self.all_permissions.append(assign_any_user)

        assign_any_organization = Permission(
            name='assign_any_organization',
            description='Assign any organization to resources'
        )
        self.all_permissions.append(assign_any_organization)

        # Assign license permissions
        assign_standard_license = Permission(
            name='assign_standard_license',
            description='Assign standard license'
        )
        self.all_permissions.append(assign_standard_license)

        assign_advanced_license = Permission(
            name='assign_advanced_license',
            description='Assign advanced license'
        )
        self.all_permissions.append(assign_advanced_license)

        assign_professional_license = Permission(
            name='assign_professional_license',
            description='Assign professional license'
        )
        self.all_permissions.append(assign_professional_license)

        assign_enterprise_license = Permission(
            name='assign_enterprise_license',
            description='Assign enterprise license'
        )
        self.all_permissions.append(assign_enterprise_license)

        assign_any_license = Permission(
            name='assign_any_license',
            description='Assign any license'
        )
        self.all_permissions.append(assign_any_license)

        # Map View Permissions
        remove_layers = Permission(
            name='remove_layers',
            description='Remove layers from map views'
        )
        self.all_permissions.append(remove_layers)

        rename_layers = Permission(
            name='rename_layers',
            description='Rename layers from map views'
        )
        self.all_permissions.append(rename_layers)

        toggle_public_layers = Permission(
            name='toggle_public_layers',
            description='Toggle layers from map views for public viewing'
        )
        self.all_permissions.append(toggle_public_layers)

        # Only add enabled permissions groups
        enabled_permissions_groups = self.permission_manager.list()

        # Standard User -----------------------------------------------------------------------------------------------#
        if self.permission_manager.STD_U_PERMS in enabled_permissions_groups:
            standard_user_perms = [
                view_resource_details,
                view_organizations,
                view_resources
            ]

            # Add custom permissions
            standard_user_perms += self.custom_permissions[self.permission_manager.STD_U_PERMS]

            # Define role/permissions group
            has_standard_user_role = Permission(
                name='has_standard_user_role',
                description='Has Standard User role'
            )

            standard_user_role = PermissionGroup(
                name=self.permission_manager.STD_U_PERMS,
                permissions=standard_user_perms + [has_standard_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.STD_U_PERMS] = standard_user_perms
            self.permissions_groups[self.permission_manager.STD_U_PERMS] = standard_user_role
            self.all_permissions_groups.append(standard_user_role)

        # Standard Admin ----------------------------------------------------------------------------------------------#
        if self.permission_manager.STD_A_PERMS in enabled_permissions_groups:
            standard_admin_perms = standard_user_perms + [
                create_resource, edit_resource, delete_resource,
                view_users, modify_users, modify_organization_members,
                assign_org_users_role, assign_org_admin_role,
                remove_layers, rename_layers, toggle_public_layers
            ]

            # Add custom permissions
            standard_admin_perms += self.custom_permissions[self.permission_manager.STD_A_PERMS]

            # Define role/permissions group
            has_standard_admin_role = Permission(
                name='has_standard_admin_role',
                description='Has Standard Admin role'
            )

            standard_admin_role = PermissionGroup(
                name=self.permission_manager.STD_A_PERMS,
                permissions=standard_admin_perms + [has_standard_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.STD_A_PERMS] = standard_admin_perms
            self.permissions_groups[self.permission_manager.STD_A_PERMS] = standard_admin_role
            self.all_permissions_groups.append(standard_admin_role)

        # Advanced User -----------------------------------------------------------------------------------------------#
        if self.permission_manager.ADV_U_PERMS in enabled_permissions_groups:
            advanced_user_perms = standard_user_perms

            # Add custom permissions
            advanced_user_perms += self.custom_permissions[self.permission_manager.ADV_U_PERMS]

            # Define role/permissions group
            has_advanced_user_role = Permission(
                name='has_advanced_user_role',
                description='Has Advanced User role'
            )

            advanced_user_role = PermissionGroup(
                name=self.permission_manager.ADV_U_PERMS,
                permissions=advanced_user_perms + [has_advanced_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ADV_U_PERMS] = advanced_user_perms
            self.permissions_groups[self.permission_manager.ADV_U_PERMS] = advanced_user_role
            self.all_permissions_groups.append(advanced_user_role)

        # Advanced Admin ----------------------------------------------------------------------------------------------#
        if self.permission_manager.ADV_A_PERMS in enabled_permissions_groups:
            advanced_admin_perms = standard_admin_perms + advanced_user_perms

            # Add custom permissions
            advanced_admin_perms += self.custom_permissions[self.permission_manager.ADV_A_PERMS]

            # Define role/permissions group
            has_advanced_admin_role = Permission(
                name='has_advanced_admin_role',
                description='Has Advanced Admin role'
            )

            advanced_admin_role = PermissionGroup(
                name=self.permission_manager.ADV_A_PERMS,
                permissions=advanced_admin_perms + [has_advanced_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ADV_A_PERMS] = advanced_admin_perms
            self.permissions_groups[self.permission_manager.ADV_A_PERMS] = advanced_admin_role
            self.all_permissions_groups.append(advanced_admin_role)

        # Professional User -------------------------------------------------------------------------------------------#
        if self.permission_manager.PRO_U_PERMS in enabled_permissions_groups:
            professional_user_perms = advanced_user_perms

            # Add custom permissions
            professional_user_perms += self.custom_permissions[self.permission_manager.PRO_U_PERMS]

            # Define role/permissions group
            has_professional_user_role = Permission(
                name='has_professional_user_role',
                description='Has Professional User role'
            )

            professional_user_role = PermissionGroup(
                name=self.permission_manager.PRO_U_PERMS,
                permissions=professional_user_perms + [has_professional_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.PRO_U_PERMS] = professional_user_perms
            self.permissions_groups[self.permission_manager.PRO_U_PERMS] = professional_user_role
            self.all_permissions_groups.append(professional_user_role)

        # Professional Admin ------------------------------------------------------------------------------------------#
        if self.permission_manager.PRO_A_PERMS in enabled_permissions_groups:
            professional_admin_perms = advanced_admin_perms + professional_user_perms

            # Add custom permissions
            professional_admin_perms += self.custom_permissions[self.permission_manager.PRO_A_PERMS]

            # Define role/permissions group
            has_professional_admin_role = Permission(
                name='has_professional_admin_role',
                description='Has Professional Admin role'
            )

            professional_admin_role = PermissionGroup(
                name=self.permission_manager.PRO_A_PERMS,
                permissions=professional_admin_perms + [has_professional_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.PRO_A_PERMS] = professional_admin_perms
            self.permissions_groups[self.permission_manager.PRO_A_PERMS] = professional_admin_role
            self.all_permissions_groups.append(professional_admin_role)

        # Enterprise User ---------------------------------------------------------------------------------------------#
        if self.permission_manager.ENT_U_PERMS in enabled_permissions_groups:
            enterprise_user_perms = professional_user_perms

            # Add custom permissions
            enterprise_user_perms += self.custom_permissions[self.permission_manager.ENT_U_PERMS]

            # Define role/permissions group
            has_enterprise_user_role = Permission(
                name='has_enterprise_user_role',
                description='Has Enterprise User role'
            )

            enterprise_user_role = PermissionGroup(
                name=self.permission_manager.ENT_U_PERMS,
                permissions=enterprise_user_perms + [has_enterprise_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ENT_U_PERMS] = enterprise_user_perms
            self.permissions_groups[self.permission_manager.ENT_U_PERMS] = enterprise_user_role
            self.all_permissions_groups.append(enterprise_user_role)

        # Enterprise Admin --------------------------------------------------------------------------------------------#
        if self.permission_manager.ENT_A_PERMS in enabled_permissions_groups:
            enterprise_admin_perms = professional_admin_perms + enterprise_user_perms + [
                create_organizations, edit_organizations, assign_advanced_license,
                assign_standard_license, assign_professional_license,
            ]

            # Add custom permissions
            enterprise_admin_perms += self.custom_permissions[self.permission_manager.ENT_A_PERMS]

            # Define role/permissions group
            has_enterprise_admin_role = Permission(
                name='has_enterprise_admin_role',
                description='Has Enterprise Admin role'
            )

            enterprise_admin_role = PermissionGroup(
                name=self.permission_manager.ENT_A_PERMS,
                permissions=enterprise_admin_perms + [has_enterprise_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ENT_A_PERMS] = enterprise_admin_perms
            self.permissions_groups[self.permission_manager.ENT_A_PERMS] = enterprise_admin_role
            self.all_permissions_groups.append(enterprise_admin_role)

        # App Admin ---------------------------------------------------------------------------------------------------#
        if self.permission_manager.APP_A_PERMS in enabled_permissions_groups:
            app_admin_perms = [
                view_resource_details, view_resources, view_all_resources, create_resource,
                edit_resource, delete_resource, always_delete_resource,
                modify_user_manager, modify_users, view_users, view_all_users, assign_org_users_role,
                assign_org_admin_role, assign_app_admin_role, assign_developer_role, view_organizations,
                view_all_organizations, create_organizations, edit_organizations, delete_organizations,
                modify_organization_members,
                assign_any_resource, assign_any_organization, assign_any_user, assign_advanced_license,
                assign_standard_license, assign_professional_license, assign_enterprise_license, assign_any_license
            ]

            # Add custom permissions
            app_admin_perms += self.custom_permissions[self.permission_manager.APP_A_PERMS]

            # Define role/permissions group
            has_app_admin_role = Permission(
                name='has_app_admin_role',
                description='Has app admin role'
            )

            app_admin_role = PermissionGroup(
                name=self.permission_manager.APP_A_PERMS,
                permissions=app_admin_perms + [has_app_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.APP_A_PERMS] = app_admin_perms
            self.permissions_groups[self.permission_manager.APP_A_PERMS] = app_admin_role
            self.all_permissions_groups.append(app_admin_role)

        return self.all_permissions_groups
