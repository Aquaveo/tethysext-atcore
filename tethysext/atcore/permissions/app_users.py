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
        # 1. Define All Permissions -----------------------------------------------------------------------------------#

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

        assign_org_user_role = Permission(
            name='assign_org_user_role',
            description='Assign organization user role'
        )
        self.all_permissions.append(assign_org_user_role)

        assign_org_reviewer_role = Permission(
            name='assign_org_reviewer_role',
            description='Assign organization reviewer role'
        )
        self.all_permissions.append(assign_org_reviewer_role)

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

        assign_consultant_license = Permission(
            name='assign_consultant_license',
            description='Assign consultant license'
        )
        self.all_permissions.append(assign_consultant_license)

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

        use_map_plot = Permission(
            name='use_map_plot',
            description='Can use the plotting feature on map views.'
        )
        self.all_permissions.append(use_map_plot)

        use_map_geocode = Permission(
            name='use_map_geocode',
            description='Can use the geocoding feature on map views.'
        )
        self.all_permissions.append(use_map_geocode)

        # Lock permissions
        can_override_user_locks = Permission(
            name='can_override_user_locks',
            description='Can override user locks on workflows.'
        )
        self.all_permissions.append(can_override_user_locks)

        # Download layer permissions
        can_download = Permission(
            name='can_download',
            description='Can download layer in map view.'
        )
        self.all_permissions.append(can_download)

        # Download layer permissions
        can_export_datatable = Permission(
            name='can_export_datatable',
            description='Can download layer in map view.'
        )
        self.all_permissions.append(can_export_datatable)

        # Only add enabled permissions groups
        enabled_permissions_groups = self.permission_manager.list()

        # 2. Collect Permissions --------------------------------------------------------------------------------------#

        # Standard User -----------------------------------------------------------------------------------------------#
        standard_user_perms = [view_resource_details, view_organizations, view_resources, use_map_plot, use_map_geocode]

        if self.permission_manager.STD_U_PERMS in self.custom_permissions:
            standard_user_perms += self.custom_permissions[self.permission_manager.STD_U_PERMS]

        # Standard Reviewer -------------------------------------------------------------------------------------------#
        standard_reviewer_perms = standard_user_perms

        if self.permission_manager.STD_R_PERMS in self.custom_permissions:
            standard_reviewer_perms += self.custom_permissions[self.permission_manager.STD_R_PERMS]

        # Standard Admin ----------------------------------------------------------------------------------------------#
        standard_admin_perms = standard_user_perms + [
            create_resource, edit_resource, delete_resource,
            view_users, modify_users, modify_organization_members,
            assign_org_user_role, assign_org_reviewer_role, assign_org_admin_role,
            remove_layers, rename_layers, toggle_public_layers,
            can_override_user_locks, can_download, can_export_datatable
        ]

        if self.permission_manager.STD_A_PERMS in self.custom_permissions:
            standard_admin_perms += self.custom_permissions[self.permission_manager.STD_A_PERMS]

        # Advanced User -----------------------------------------------------------------------------------------------#
        advanced_user_perms = standard_user_perms

        if self.permission_manager.ADV_U_PERMS in self.custom_permissions:
            advanced_user_perms += self.custom_permissions[self.permission_manager.ADV_U_PERMS]

        # Advanced Reviewer -------------------------------------------------------------------------------------------#
        advanced_reviewer_perms = advanced_user_perms

        if self.permission_manager.ADV_R_PERMS in self.custom_permissions:
            advanced_reviewer_perms += self.custom_permissions[self.permission_manager.ADV_R_PERMS]

        # Advanced Admin ----------------------------------------------------------------------------------------------#
        advanced_admin_perms = standard_admin_perms + advanced_user_perms

        if self.permission_manager.ADV_A_PERMS in self.custom_permissions:
            advanced_admin_perms += self.custom_permissions[self.permission_manager.ADV_A_PERMS]

        # Professional User -------------------------------------------------------------------------------------------#
        professional_user_perms = advanced_user_perms

        if self.permission_manager.PRO_U_PERMS in self.custom_permissions:
            professional_user_perms += self.custom_permissions[self.permission_manager.PRO_U_PERMS]

        # Professional Reviewer ---------------------------------------------------------------------------------------#
        professional_reviewer_perms = professional_user_perms

        if self.permission_manager.PRO_R_PERMS in self.custom_permissions:
            professional_reviewer_perms += self.custom_permissions[self.permission_manager.PRO_R_PERMS]

        # Professional Admin ------------------------------------------------------------------------------------------#
        professional_admin_perms = advanced_admin_perms + professional_user_perms

        if self.permission_manager.PRO_A_PERMS in self.custom_permissions:
            professional_admin_perms += self.custom_permissions[self.permission_manager.PRO_A_PERMS]

        # Consultant User ---------------------------------------------------------------------------------------------#
        consultant_user_perms = professional_user_perms

        if self.permission_manager.CON_U_PERMS in self.custom_permissions:
            consultant_user_perms += self.custom_permissions[self.permission_manager.CON_U_PERMS]

        # Consultant Reviewer Role ------------------------------------------------------------------------------------#
        consultant_reviewer_perms = professional_user_perms

        if self.permission_manager.CON_R_PERMS in self.custom_permissions:
            consultant_reviewer_perms += self.custom_permissions[self.permission_manager.CON_R_PERMS]

        # Consultant Admin --------------------------------------------------------------------------------------------#
        consultant_admin_perms = professional_admin_perms + consultant_user_perms + [
            create_organizations, edit_organizations, assign_advanced_license,
            assign_standard_license, assign_professional_license, can_download, can_export_datatable
        ]

        if self.permission_manager.CON_A_PERMS in self.custom_permissions:
            consultant_admin_perms += self.custom_permissions[self.permission_manager.CON_A_PERMS]

        # App Admin ---------------------------------------------------------------------------------------------------#
        app_admin_perms = self.all_permissions

        if self.permission_manager.APP_A_PERMS in self.custom_permissions:
            app_admin_perms += self.custom_permissions[self.permission_manager.APP_A_PERMS]

        # 3. Create Permission Groups/Roles ---------------------------------------------------------------------------#
        has_org_user_role = Permission(
            name=self.permission_manager.get_has_role_permission_for(
                role=self.permission_manager.ROLES.ORG_USER
            ),
            description='Has Organization User role.'
        )

        has_org_reviewer_role = Permission(
            name=self.permission_manager.get_has_role_permission_for(
                role=self.permission_manager.ROLES.ORG_REVIEWER
            ),
            description='Has Organization Reviewer role.'
        )

        has_org_admin_role = Permission(
            name=self.permission_manager.get_has_role_permission_for(
                role=self.permission_manager.ROLES.ORG_ADMIN
            ),
            description='Has Organization Admin role.'
        )

        # Standard User Role ------------------------------------------------------------------------------------------#
        if self.permission_manager.STD_U_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_standard_user_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_USER,
                    license=self.permission_manager.LICENSES.STANDARD
                ),
                description='Has Standard User role'
            )

            standard_user_role = PermissionGroup(
                name=self.permission_manager.STD_U_PERMS,
                permissions=standard_user_perms + [has_standard_user_role, has_org_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.STD_U_PERMS] = standard_user_perms
            self.permissions_groups[self.permission_manager.STD_U_PERMS] = standard_user_role
            self.all_permissions_groups.append(standard_user_role)

        # Standard Reviewer Role --------------------------------------------------------------------------------------#
        if self.permission_manager.STD_R_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_standard_reviewer_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_REVIEWER,
                    license=self.permission_manager.LICENSES.STANDARD
                ),
                description='Has Standard Reviewer role'
            )

            standard_reviewer_role = PermissionGroup(
                name=self.permission_manager.STD_R_PERMS,
                permissions=standard_reviewer_perms + [has_standard_reviewer_role, has_org_reviewer_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.STD_R_PERMS] = standard_reviewer_perms
            self.permissions_groups[self.permission_manager.STD_R_PERMS] = standard_reviewer_role
            self.all_permissions_groups.append(standard_reviewer_role)

        # Standard Admin Role -----------------------------------------------------------------------------------------#
        if self.permission_manager.STD_A_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_standard_admin_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_ADMIN,
                    license=self.permission_manager.LICENSES.STANDARD
                ),
                description='Has Standard Admin role'
            )

            standard_admin_role = PermissionGroup(
                name=self.permission_manager.STD_A_PERMS,
                permissions=standard_admin_perms + [has_standard_admin_role, has_org_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.STD_A_PERMS] = standard_admin_perms
            self.permissions_groups[self.permission_manager.STD_A_PERMS] = standard_admin_role
            self.all_permissions_groups.append(standard_admin_role)

        # Advanced User Role ------------------------------------------------------------------------------------------#
        if self.permission_manager.ADV_U_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_advanced_user_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_USER,
                    license=self.permission_manager.LICENSES.ADVANCED
                ),
                description='Has Advanced User role'
            )

            advanced_user_role = PermissionGroup(
                name=self.permission_manager.ADV_U_PERMS,
                permissions=advanced_user_perms + [has_advanced_user_role, has_org_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ADV_U_PERMS] = advanced_user_perms
            self.permissions_groups[self.permission_manager.ADV_U_PERMS] = advanced_user_role
            self.all_permissions_groups.append(advanced_user_role)

        # Advanced Reviewer Role --------------------------------------------------------------------------------------#
        if self.permission_manager.ADV_R_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_advanced_reviewer_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_REVIEWER,
                    license=self.permission_manager.LICENSES.ADVANCED
                ),
                description='Has Advanced Reviewer role'
            )

            advanced_reviewer_role = PermissionGroup(
                name=self.permission_manager.ADV_R_PERMS,
                permissions=advanced_reviewer_perms + [has_advanced_reviewer_role, has_org_reviewer_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ADV_R_PERMS] = advanced_reviewer_perms
            self.permissions_groups[self.permission_manager.ADV_R_PERMS] = advanced_reviewer_role
            self.all_permissions_groups.append(advanced_reviewer_role)

        # Advanced Admin Role -----------------------------------------------------------------------------------------#
        if self.permission_manager.ADV_A_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_advanced_admin_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_ADMIN,
                    license=self.permission_manager.LICENSES.ADVANCED
                ),
                description='Has Advanced Admin role'
            )

            advanced_admin_role = PermissionGroup(
                name=self.permission_manager.ADV_A_PERMS,
                permissions=advanced_admin_perms + [has_advanced_admin_role, has_org_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.ADV_A_PERMS] = advanced_admin_perms
            self.permissions_groups[self.permission_manager.ADV_A_PERMS] = advanced_admin_role
            self.all_permissions_groups.append(advanced_admin_role)

        # Professional User Role --------------------------------------------------------------------------------------#
        if self.permission_manager.PRO_U_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_professional_user_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_USER,
                    license=self.permission_manager.LICENSES.PROFESSIONAL
                ),
                description='Has Professional User role'
            )

            professional_user_role = PermissionGroup(
                name=self.permission_manager.PRO_U_PERMS,
                permissions=professional_user_perms + [has_professional_user_role, has_org_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.PRO_U_PERMS] = professional_user_perms
            self.permissions_groups[self.permission_manager.PRO_U_PERMS] = professional_user_role
            self.all_permissions_groups.append(professional_user_role)

        # Professional Reviewer Role ----------------------------------------------------------------------------------#
        if self.permission_manager.PRO_R_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_professional_reviewer_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_REVIEWER,
                    license=self.permission_manager.LICENSES.PROFESSIONAL
                ),
                description='Has Professional Reviewer role'
            )

            professional_reviewer_role = PermissionGroup(
                name=self.permission_manager.PRO_R_PERMS,
                permissions=professional_reviewer_perms + [has_professional_reviewer_role, has_org_reviewer_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.PRO_R_PERMS] = professional_reviewer_perms
            self.permissions_groups[self.permission_manager.PRO_R_PERMS] = professional_reviewer_role
            self.all_permissions_groups.append(professional_reviewer_role)

        # Professional Admin Role -------------------------------------------------------------------------------------#
        if self.permission_manager.PRO_A_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_professional_admin_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_ADMIN,
                    license=self.permission_manager.LICENSES.PROFESSIONAL
                ),
                description='Has Professional Admin role'
            )

            professional_admin_role = PermissionGroup(
                name=self.permission_manager.PRO_A_PERMS,
                permissions=professional_admin_perms + [has_professional_admin_role, has_org_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.PRO_A_PERMS] = professional_admin_perms
            self.permissions_groups[self.permission_manager.PRO_A_PERMS] = professional_admin_role
            self.all_permissions_groups.append(professional_admin_role)

        # Consultant User Role ----------------------------------------------------------------------------------------#
        if self.permission_manager.CON_U_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_consultant_user_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_USER,
                    license=self.permission_manager.LICENSES.CONSULTANT
                ),
                description='Has Consultant User role'
            )

            consultant_user_role = PermissionGroup(
                name=self.permission_manager.CON_U_PERMS,
                permissions=consultant_user_perms + [has_consultant_user_role, has_org_user_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.CON_U_PERMS] = consultant_user_perms
            self.permissions_groups[self.permission_manager.CON_U_PERMS] = consultant_user_role
            self.all_permissions_groups.append(consultant_user_role)

        # Consultant Reviewer Role ------------------------------------------------------------------------------------#
        if self.permission_manager.CON_R_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_consultant_reviewer_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_REVIEWER,
                    license=self.permission_manager.LICENSES.CONSULTANT
                ),
                description='Has Consultant Reviewer role'
            )

            consultant_reviewer_role = PermissionGroup(
                name=self.permission_manager.CON_R_PERMS,
                permissions=consultant_reviewer_perms + [has_consultant_reviewer_role, has_org_reviewer_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.CON_R_PERMS] = consultant_reviewer_perms
            self.permissions_groups[self.permission_manager.CON_R_PERMS] = consultant_reviewer_role
            self.all_permissions_groups.append(consultant_reviewer_role)

        # Consultant Admin Role ---------------------------------------------------------------------------------------#
        if self.permission_manager.CON_A_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_consultant_admin_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.ORG_ADMIN,
                    license=self.permission_manager.LICENSES.CONSULTANT
                ),
                description='Has Consultant Admin role'
            )

            consultant_admin_role = PermissionGroup(
                name=self.permission_manager.CON_A_PERMS,
                permissions=consultant_admin_perms + [has_consultant_admin_role, has_org_admin_role]
            )

            # Save for later use
            self.permissions[self.permission_manager.CON_A_PERMS] = consultant_admin_perms
            self.permissions_groups[self.permission_manager.CON_A_PERMS] = consultant_admin_role
            self.all_permissions_groups.append(consultant_admin_role)

        # App Admin Role ----------------------------------------------------------------------------------------------#
        if self.permission_manager.APP_A_PERMS in enabled_permissions_groups:
            # Define role/permissions group
            has_app_admin_role = Permission(
                name=self.permission_manager.get_has_role_permission_for(
                    role=self.permission_manager.ROLES.APP_ADMIN
                ),
                description='Has App Admin role'
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
