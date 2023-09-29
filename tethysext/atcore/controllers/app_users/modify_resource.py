"""
********************************************************************************
* Name: modify_resource.py
* Author: nswain
* Created On: April 18, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import traceback
import logging
# Django
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
# Tethys core
from tethys_sdk.permissions import permission_required, has_permission
from tethys_apps.utilities import get_active_app
from tethys_gizmos.gizmo_options import TextInput, SelectInput
# ATCore
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.gizmos import SpatialReferenceSelect
from tethysext.atcore.services.spatial_reference import SpatialReferenceService

log = logging.getLogger(f'tethys.{__name__}')


class ModifyResource(ResourceViewMixin):
    """
    Controller for modify_resource page.

    GET: Render form for adding/editing resource.
    POST: Handle form submission to add/edit a new resource.
    """
    page_title = 'Add Resource'
    template_name = 'atcore/app_users/modify_resource.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get', 'post']

    # Srid field options
    include_srid = False
    srid_required = False
    srid_default = ""
    srid_error = "Spatial reference is required."

    # File upload options
    include_file_upload = False
    file_upload_required = False
    file_upload_multiple = False
    file_upload_accept = ""
    file_upload_label = "Input Files" if file_upload_multiple else "Input File"
    file_upload_help = "Upload files associated with this resource."
    file_upload_error = "Must provide file(s)."

    # Relationship fields options
    enable_relationship_fields = False
    parents_field_label = None
    children_field_label = None
    show_parents_field_on_edit = True
    show_children_field_on_edit = True
    show_parents_field_on_new = True
    show_children_field_on_new = True

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_modify_resource_requests(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        return self._handle_modify_resource_requests(request, *args, **kwargs)

    @active_user_required()
    @permission_required('create_resource', 'edit_resource', use_or=True)
    def _handle_modify_resource_requests(self, request, resource_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # Defaults
        valid = True
        resource = None
        context = dict()
        resource_name = ""
        resource_name_error = ""
        resource_description = ""
        resource_srid = self.srid_default
        resource_srid_text = ""
        resource_srid_error = ""
        selected_organizations = list()
        organization_select_error = ""
        selected_parents = list()
        parents_select_error = ""
        selected_children = list()
        children_select_error = ""
        file_upload_error = ""

        # GET params
        next_arg = str(request.GET.get('next', ""))
        active_app = get_active_app(request)
        app_namespace = active_app.url_namespace

        # Set redirect url
        if next_arg == 'manage-organizations':
            next_controller = '{}:app_users_manage_organizations'.format(app_namespace)
        else:
            next_controller = f'{app_namespace}:{_Resource.SLUG}_manage_resources'

        # If ID is provided, then we are editing, otherwise we are creating a new resource
        editing = resource_id is not None
        creating = not editing

        if editing:
            enable_parents_field = self.show_parents_field_on_edit
            enable_children_field = self.show_children_field_on_edit
        else:
            enable_parents_field = self.show_parents_field_on_new
            enable_children_field = self.show_children_field_on_new

        try:
            # Check if can create resources
            can_create_resource, msg = self.can_create_resource(session, request, request_app_user)

            if creating and not can_create_resource:
                raise ATCoreException(msg)

            # Process form submission
            if request.POST and 'modify-resource-submit' in request.POST:
                # POST params
                post_params = request.POST
                resource_name = post_params.get('resource-name', "")
                resource_description = post_params.get('resource-description', "")
                resource_srid = post_params.get('spatial-ref-select', self.srid_default)
                selected_organizations = post_params.getlist('assign-organizations', [])
                selected_parents = post_params.getlist('assign-parents', [])
                selected_children = post_params.getlist('assign-children', [])
                files = request.FILES

                # Validate
                if not resource_name:
                    valid = False
                    resource_name_error = "Must specify a name for the {}.".format(
                        _Resource.DISPLAY_TYPE_SINGULAR.lower()
                    )

                # Must assign project to at least one organization
                if len(selected_organizations) < 1:
                    valid = False
                    organization_select_error = f"Must assign {_Resource.DISPLAY_TYPE_SINGULAR.lower()} " \
                        "to at least one organization."

                if creating and self.include_file_upload and self.file_upload_required \
                   and 'input-file-upload' not in files:
                    valid = False
                    file_upload_error = self.file_upload_error

                if creating and self.include_srid and self.srid_required \
                   and not resource_srid:
                    valid = False
                    resource_srid_error = self.srid_error

                custom_valid, custom_fields_errors = self.validate_custom_fields(post_params,
                                                                                 session,
                                                                                 request,
                                                                                 request_app_user)
                context.update(custom_fields_errors)

                if valid and custom_valid:
                    # Look up existing resource
                    if editing:
                        resource = session.query(_Resource).get(resource_id)

                        if not resource:
                            raise ATCoreException('Unable to find {}'.format(
                                _Resource.DISPLAY_TYPE_SINGULAR.lower()
                            ))

                        # Reset the organizations
                        resource.organizations = []

                        # Reset the parents
                        resource.parents = []

                        # Reset the children
                        resource.children = []

                    # Otherwise create a new project
                    else:
                        resource = _Resource()

                    # Assign name and description
                    resource.name = resource_name
                    resource.description = resource_description

                    # Assign project to organizations
                    for organization_id in selected_organizations:
                        organization = session.query(_Organization).get(organization_id)
                        if organization:
                            resource.organizations.append(organization)

                    if self.enable_relationship_fields:
                        # Assign parents to resource
                        if enable_parents_field and selected_parents:
                            parents = session.query(_Resource) \
                                .filter(_Resource.id.in_(selected_parents)) \
                                .all()
                            resource.parents.extend(parents)

                        # Assign children to resource
                        if enable_children_field and selected_children:
                            children = session.query(_Resource) \
                                .filter(_Resource.id.in_(selected_children)) \
                                .all()
                            resource.children.extend(children)

                    # Assign spatial reference id, handling change if editing
                    if self.include_srid:
                        old_srid = resource.get_attribute('srid')
                        srid_changed = resource_srid != old_srid
                        resource.set_attribute('srid', resource_srid)

                        if editing and srid_changed:
                            self.handle_srid_changed(session, request, request_app_user, resource, old_srid,
                                                     resource_srid)

                    # Only do the following if creating a new project
                    if creating:
                        # Set created by
                        resource.created_by = request_app_user.username

                        # Save resource
                        session.commit()

                        # Handle file upload
                        if self.include_file_upload:
                            self.handle_file_upload(session, request, request_app_user, files, resource)

                    session.commit()

                    # Call post processing hook
                    self.handle_resource_finished_processing(
                        session, request, request_app_user, resource, editing, context
                    )

                    # Sessions are closed in the finally block
                    return redirect(reverse(next_controller))

            # Setup edit form fields
            if editing:
                # Get existing resource
                resource = session.query(_Resource).get(resource_id)
                can_edit_resource, msg = self.can_edit_resource(session, request, request_app_user, resource)

                if not can_edit_resource:
                    raise ATCoreException(msg)

                # Initialize the parameters from the existing consultant
                resource_name = resource.name
                resource_description = resource.description

                if self.include_srid:
                    resource_srid = resource.get_attribute('srid')

                # Get organizations of resource
                for organization in resource.organizations:
                    if organization.active or request.user.is_staff or has_permission(request, 'has_app_admin_role'):
                        selected_organizations.append(str(organization.id))

                if self.enable_relationship_fields:
                    if enable_parents_field:
                        # Get parents of resource
                        selected_parents = [p.id for p in resource.parents]

                    if enable_children_field:
                        # Get children of resource
                        selected_children = [c.id for c in resource.children]

            # Define form
            resource_name_input = TextInput(
                display_text='Name',
                name='resource-name',
                placeholder='e.g.: My {}'.format(_Resource.DISPLAY_TYPE_SINGULAR.title()),
                initial=resource_name,
                error=resource_name_error,
                classes='mb-3',
            )

            # Initial spatial reference value
            srid_initial = None

            if resource_srid:
                srs = SpatialReferenceService(session)
                possible_srids = srs.get_spatial_reference_system_by_srid(resource_srid)['results']
                resource_srid_text = possible_srids[0]['text'] if len(possible_srids) > 0 else ''

            if resource_srid_text and resource_srid:
                srid_initial = (resource_srid_text, resource_srid)

            # Spatial reference service/url
            spatial_reference_controller = '{}:atcore_query_spatial_reference'.format(app_namespace)
            spatial_reference_url = reverse(spatial_reference_controller)

            # Spatial reference select gizmo
            spatial_reference_select = SpatialReferenceSelect(
                display_name='Spatial Reference System',
                name='spatial-ref-select',
                placeholder='Spatial Reference System',
                min_length=2,
                query_delay=500,
                initial=srid_initial,
                error=resource_srid_error,
                spatial_reference_service=spatial_reference_url,
                classes='mb-3',
            )

            # Populate organizations select
            organization_options = request_app_user.get_organizations(session, request, as_options=True)

            organization_select = SelectInput(
                display_text='Organization(s)',
                name='assign-organizations',
                multiple=True,
                initial=selected_organizations,
                options=organization_options,
                error=organization_select_error
            )

            # Populate parents and children selects
            parents_select = None
            children_select = None
            if self.enable_relationship_fields:
                app_user_organizations_ids = [o[1] for o in organization_options]

                # Populate parents select
                if enable_parents_field:
                    parents_options = self.get_parents_select_options(
                        session=session,
                        request=request,
                        request_app_user=request_app_user,
                        resource=resource,
                        app_user_organizations=app_user_organizations_ids,
                    )

                    parent_select_label = (
                        f'Parent {_Resource.DISPLAY_TYPE_PLURAL}'
                        if not self.parents_field_label
                        else self.parents_field_label
                    )

                    parents_select = SelectInput(
                        display_text=parent_select_label,
                        name='assign-parents',
                        multiple=True,
                        initial=selected_parents,
                        options=parents_options,
                        error=parents_select_error,
                    )

                # Populate children select, excluding:
                # self, resources not in the same organization(s), resources with children
                if enable_children_field:
                    children_options = self.get_child_select_options(
                        session=session,
                        request=request,
                        request_app_user=request_app_user,
                        resource=resource,
                        app_user_organizations=app_user_organizations_ids,
                    )

                    children_select_label = (
                        f'Child {_Resource.DISPLAY_TYPE_PLURAL}'
                        if not self.children_field_label
                        else self.children_field_label
                    )

                    children_select = SelectInput(
                        display_text=children_select_label,
                        name='assign-children',
                        multiple=True,
                        initial=selected_children,
                        options=children_options,
                        error=children_select_error,
                    )

            # Initialize custom fields
            custom_fields = self.initialize_custom_fields(session, request, resource, editing, context)
            context.update(custom_fields)

        except Exception as e:
            session and session.rollback()

            if type(e) is ATCoreException:
                error_message = str(e)
            else:
                traceback.print_exc()
                error_message = ("An unexpected error occurred while uploading your project. Please try again or "
                                 "contact support@aquaveo.com for further assistance.")
            log.exception(error_message)
            messages.error(request, error_message)

            # Sessions closed in finally block
            return redirect(reverse(next_controller))

        finally:
            # Close sessions
            session and session.close()

        context.update({
            'next_controller': next_controller,
            'editing': editing,
            'type_singular': _Resource.DISPLAY_TYPE_SINGULAR,
            'type_plural': _Resource.DISPLAY_TYPE_PLURAL,
            'resource_name_input': resource_name_input,
            'organization_select': organization_select,
            'parents_select': parents_select,
            'children_select': children_select,
            'resource_description': resource_description,
            'show_relationship_fields': self.enable_relationship_fields,
            'show_parents_field': enable_parents_field,
            'show_children_field': enable_children_field,
            'show_srid_field': self.include_srid,
            'spatial_reference_select': spatial_reference_select,
            'show_file_upload_field': self.include_file_upload and creating,
            'file_upload_multiple': self.file_upload_multiple,
            'file_upload_error': file_upload_error,
            'file_upload_label': self.file_upload_label,
            'file_upload_help': self.file_upload_help,
            'file_upload_accept': self.file_upload_accept,
            'base_template': self.base_template
        })

        context = self.get_context(request, context, editing)

        return render(request, self.template_name, context)

    def can_create_resource(self, session, request, request_app_user):
        """
        Check performed when determining if a new resource can be created, considering permissions and other factors (i.e. storage).  # noqa: E501
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.

        Returns:
            bool: True if the request app users is able to created a new resource, else false.
            str: Error message to display if False.
        """
        _Resource = self.get_resource_model()
        error_message = "We're sorry, but you are not able to create {} at this time.".format(
            _Resource.DISPLAY_TYPE_PLURAL.lower()
        )
        return has_permission(request, 'create_resource'), error_message

    def can_edit_resource(self, session, request, request_app_user, resource):
        """

        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            resource(Resource): The resource being edited.

        Returns:
            bool: True if can edit, else false.
        """
        _Resource = self.get_resource_model()
        error_message = "We're sorry, but you are not allowed to edit this {}.".format(
            _Resource.DISPLAY_TYPE_PLURAL.lower()
        )
        return has_permission(request, 'edit_resource'), error_message

    def handle_file_upload(self, session, request, request_app_user, files, resource):
        """
        Handle file uploads. Raise an ATCoreException if issue occur.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            files(request.FILES): Django in-memory files object.
            resource(Resource): The newly created resource.
        """
        app_workspace = self._app.get_app_workspace().path
        file_upload_dir = os.path.join(app_workspace, str(resource.id))

        # Create job directory if it doesn't exist already
        if not os.path.exists(file_upload_dir):
            os.makedirs(file_upload_dir)

            upload_files = files.getlist('input-file-upload')
            filenames = []
            for upload_file in upload_files:
                filename = os.path.join(file_upload_dir, upload_file.name)
                with open(filename, 'wb+') as destination:
                    for chunk in upload_file.chunks():
                        destination.write(chunk)
                filenames.append(filename)

        resource.set_attribute('files', filenames)

    def get_parents_select_options(self, session, request, request_app_user, resource, app_user_organizations):
        """
        Build the list of options for the parent relationship select field.

        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            resource(Resource): The resource being edited.
            app_user_organizations (list<str>): List of organization ids to which the app user belongs.

        Returns:
            list<2-tuples<name, id>>: A list of 2-tuples, each tuple containing the name and id of a resource.
        """
        _Resource = self.get_resource_model()
        _Organization = self.get_organization_model()

        # Resource belonging to user's organization
        parents_options_query = session.query(_Resource) \
            .filter(_Resource.organizations.any(_Organization.id.in_(app_user_organizations)))

        # If resource is defined (editing) also exclude that resource
        if resource is not None:
            parents_options_query = parents_options_query.filter(_Resource.id != resource.id)

        parents_options = [(p.name, p.id) for p in parents_options_query.all()]
        return parents_options

    def get_child_select_options(self, session, request, request_app_user, resource, app_user_organizations):
        """
        Build the list of options for the child relationship select field.

        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            resource(Resource): The resource being edited.
            app_user_organizations (list<str>): List of organization ids to which the app user belongs.

        Returns:
            list<2-tuples<name, id>>: A list of 2-tuples, each tuple containing the name and id of a resource.
        """
        _Resource = self.get_resource_model()
        _Organization = self.get_organization_model()

        # Resource belonging to user's organization
        children_options_query = session.query(_Resource) \
            .filter(_Resource.organizations.any(_Organization.id.in_(app_user_organizations)))

        # If resource is defined (editing) also exclude that resource
        if resource is not None:
            children_options_query = children_options_query.filter(_Resource.id != resource.id)

        children_options = [(c.name, c.id) for c in children_options_query.all()]
        return children_options

    def handle_srid_changed(self, session, request, request_app_user, resource, old_srid, new_srid):
        """
        Handle srid changed event when editing an existing resource.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            resource(Resource): The resource being edited.
            old_srid(str): The old srid.
            new_srid(str): The new srid.
        """
        pass

    def handle_resource_finished_processing(self, session, request, request_app_user, resource, editing, context=None):
        """
        Hook to allow for post processing after the resource has finished being created or updated.
        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.
            resource(Resource): The resource being edited or newly created.
            editing(bool): True if editing, False if creating a new resource.
            contex(dict): Template context variables for the view.
        """
        pass

    def initialize_custom_fields(self, session, request, resource, editing, context=None):
        """
        Hook to allow for initializing custom fields.

        Args:
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            resource(Resource): The resource being edited.
            editing(bool): True if rendering form for editing.
            context(dict): Template context variables for the view.

        Returns:
            dict: Template context variables for defining custom fields.
        """
        return dict()

    def validate_custom_fields(self, params, session=None, request=None, request_app_user=None):
        """
        Hook to allow for validating custom fields.

        Args:
            params: The request.POST object with values submitted by user.
            session(sqlalchemy.session): open sqlalchemy session.
            request(django.request): the Django request.
            request_app_user(AppUser): app user that is making the request.

        Returns:
            bool, dict: False if any custom fields invalid, Template context variables for validation feedback (i.e. error messages).
        """  # noqa: E501
        return True, dict()

    def get_context(self, request, context, editing):
        """
        Hook to add to context.
        Args:
            context(dict): context for controller.
        """
        return context
