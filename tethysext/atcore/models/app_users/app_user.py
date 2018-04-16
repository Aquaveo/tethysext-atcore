import uuid

from sqlalchemy import Column, Boolean, String
from sqlalchemy.orm import relationship, validates, reconstructor
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.services.app_users.func import get_display_name_for_django_user
from tethysext.atcore.services.app_users.user_roles import Roles

from .associations import user_organization_association
from .base import AppUsersBase

__all__ = ['AppUser']


class AppUser(AppUsersBase):
    """
    Definition for the app_user table. All app users are associated with django users.
    """
    # User Role Properties
    ROLES = Roles()

    # Staff user defaults
    STAFF_USERNAME = '_staff_user'
    STAFF_ROLE = ROLES.DEVELOPER
    STAFF_DISPLAY_NAME = 'Developer'

    __tablename__ = 'app_users'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(String)  #: Used to map to Django user object
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    organizations = relationship('Organization',
                                 secondary=user_organization_association,
                                 back_populates='members')

    def __init__(self, *args, **kwargs):
        """
        Contstructor.
        """
        self._django_user = None

        # Call super class
        super(AppUser, self).__init__(*args, **kwargs)

    @reconstructor
    def init_on_load(self):
        """
        Contstructor for the instances loaded from database
        """
        self._django_user = None

    @validates('role')
    def validate_role(self, key, field):
        if key == 'role':
            if not self.ROLES.is_valid(field):
                raise ValueError('The value "{}" is not a valid role.'.format(field))

        return field

    @property
    def django_user(self):
        if self._django_user is None:
            self._django_user = self.get_django_user()
        return self._django_user

    @property
    def email(self):
        return self.django_user.email

    @email.setter
    def email(self, value):
        self.django_user.email = value
        self.django_user.save()

    @property
    def first_name(self):
        return self.django_user.first_name

    @first_name.setter
    def first_name(self, value):
        self.django_user.first_name = value
        self.django_user.save()

    @property
    def last_name(self):
        return self.django_user.last_name

    @last_name.setter
    def last_name(self, value):
        self.django_user.last_name = value
        self.django_user.save()

    @classmethod
    def get_app_user_from_request(cls, request, session, redirect_if_invalid=True):
        """
        Get the AppUser cooresponding with the request user and redirect if no app user exists.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object.
            request(django.request): Django request object.
            redirect_if_invalid (bool): Redirects to app library page if no app user is found for the request user.

        Returns:
            AppUser: app user cooresponding with the request user or None if one does not exist and redirect is False.
        """
        if request.user.is_staff:
            username = cls.STAFF_USERNAME
        else:
            username = request.user.username

        app_user = session.query(cls).filter(cls.username == username).one_or_none()

        # If no app user found, redirect to the apps library page and warn.
        if redirect_if_invalid:
            if app_user is None and not request.user.is_staff and redirect_if_invalid:
                from django.contrib import messages
                from django.urls import reverse
                from django.shortcuts import redirect
                messages.warning(request, "We're sorry, but you do not have an account in this app.")
                session.close()
                return redirect(reverse('app_library'))

        return app_user

    @staticmethod
    def get_organization_model():
        from organization import Organization
        return Organization

    @staticmethod
    def get_resource_model():
        from resource import Resource
        return Resource

    def is_staff(self):
        return self.username == self.STAFF_USERNAME

    def get_display_name(self, default_to_username=True, append_username=False):
        """
        Get a nice display name for an app user.
        Args:
            default_to_username: Return username if no other names are available if True.
            append_username: Append the username in parenthesis if True. e.g.: "First Last (username)".

        Returns: In order of priority: "First Last", "First", "Last", "username".
        """
        if self.django_user is None and self.is_staff():
            display_name = self.STAFF_DISPLAY_NAME
        else:
            display_name = get_display_name_for_django_user(
                self.django_user,
                default_to_username=default_to_username,
                append_username=append_username
            )
        return display_name

    def get_django_user(self):
        """
        Get the Django user object associated with this app user object

        Returns: Django User object
        """
        from django.contrib.auth.models import User
        try:
            django_user = User.objects.get(username=self.username)
        except User.DoesNotExist:
            return None
        return django_user

    def get_organizations(self, session, request, as_options=False, cascade=True, consultants=False):
        """
        Get the Organizations to which the given user belongs.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object.
            request(django.request): Django request object.
            as_options(bool): Return and select option pairs if True.
            cascade(bool): Return subordinate organizations if True.
            consultants(bool): Only organizations that can be a consultant if True.

        Returns:
            list: Organizations to which the user belongs with subordinate Organizations if cascade.
        """
        from tethys_sdk.permissions import has_permission

        _Organization = self.get_organization_model()
        return_value = set()

        if self.is_staff() or has_permission(request, 'view_all_organizations', user=self.django_user):
            user_organizations = session.query(_Organization).all()

        else:
            user_organizations = self.organizations

        organizations = set(user_organizations)

        if cascade:
            client_organizations = set()

            for organization in organizations:
                client_organizations.update(organization.clients)

            organizations.update(client_organizations)

        if consultants:
            consultant_organizations = set()

            for organization in organizations:
                if organization.can_have_clients():
                    consultant_organizations.add(organization)

            organizations = consultant_organizations

        if as_options:
            for organization in organizations:
                return_value.add((organization.name, str(organization.id)))

            return_value = sorted(return_value, key=lambda c: c[0])
        else:
            return_value = sorted(organizations, key=lambda c: c.name)

        return return_value

    def get_resources(self, session, request, of_type=None, cascade=True):
        """
        Get the resources that the request user is able to assign to clients and consultants.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object
            request(djanog.request): Django request object
            of_type(Resource): A subclass of Resource.
            cascade(bool): Also retrieve resources of child organizations.
        Returns:
        """
        from tethys_sdk.permissions import has_permission

        if of_type:
            _Resource = of_type
        else:
            _Resource = self.get_resource_model()
        resources = set()

        if self.is_staff() or has_permission(request, 'assign_any_project', user=self.django_user):
            resources = session.query(_Resource).all()

        # Other users can only assign resources that belong to their organizations
        else:
            for organization in self.get_organizations(session, request, cascade=cascade):
                org_resources = session.query(_Resource).\
                    filter(_Resource.organizations.contains(organization)).\
                    all()
                for org_rsrc in org_resources:
                    resources.add(org_rsrc)

        return self.filter_resources(resources)

    def filter_resources(self, resources):
        """
        Filter and sort the resources returned by get_resources.
        Args:
            resources: all resources that are accessible by this user.

        Returns:
            list: list of Resource objects.
        """
        # TODO: When generalizing resources, find a way to filter by status that is more generic
        # resources = [resource for resource in resources if not resource.is_deleting()]
        # resources = sorted(resources, key=lambda p: p.name)
        return resources

    def get_assignable_roles(self, request, as_options=False):
        """
        Get a list of user roles that this user can assign.

        Args:
            request: Django request object
            as_options: Returns a list of tuple pairs for use as select input options.

        Returns: list of user roles the request user can assign
        """
        from tethys_sdk.permissions import has_permission

        assignable_roles = []

        if self.is_staff():
            assignable_roles.extend(self.ROLES.list())

        else:
            for role in self.ROLES.list():
                assign_permission = self.ROLES.get_assign_permission_for(role)
                if has_permission(request, assign_permission, user=self.django_user):
                    assignable_roles.append(role)
        if as_options:
            return [(self.ROLES.get_display_name_for(r), r) for r in assignable_roles]

        return assignable_roles

    def get_peers(self, session, request, include_self=False, cascade=False):
        """
        Get AppUsers belonging to organizations to which this user belongs.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object
            request(django.request): Django request object
            include_self(bool): Include self in list of users
            cascade(bool): Also retrieve resources of child organizations.

        Returns: A list of AppUser objects.
        """
        from tethys_sdk.permissions import has_permission

        if self.is_staff() or has_permission(request, 'assign_any_user', user=self.django_user):
            return session.query(AppUser).\
                filter(AppUser.username != AppUser.STAFF_USERNAME).\
                all()

        manageable_users = set()
        organizations = self.get_organizations(session, request, cascade=cascade)

        for organization in organizations:
            for user in organization.members:
                # Don't add self to manage users
                if user.id == self.id and not include_self:
                    continue

                manageable_users.add(user)

        return manageable_users

    def update_activity(self, session, request):
        """
        Update the is_active status of this user based on the activity of the organizations to which it belongs.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object
            request(django.request): Django request object
        """
        if self.is_staff():
            return

        is_active = False
        for org in self.get_organizations(session, request, cascade=False):
            if org.active:
                is_active = True
                break
        self.is_active = is_active

    def get_role(self, display_name=False):
        """
        Get the most elevated role that has been applied to the given user.

        Args:
            display_name(bool): Return display friendly name of role if True.

        Returns: Name of role
        """
        return self.ROLES.get_display_name_for(str(self.role)) if display_name else self.role

    def update_permissions(self, session, request, permissions_manager):
        """
        Update permissions of this user based on its role and the licenses of the organizations to which it belongs.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object.
            request(django.request): Django request object.
            permissions_manager(AppPermissionsManager): Permissions manager bound to current app.
        """
        # Get models
        _Organization = self.get_organization_model()

        # Clear all epanet permissions
        permissions_manager.remove_all_permissions_groups(self)

        # App admins shouldn't belong to any organizations (i.e.: have license restrictions)
        if self.role == self.ROLES.APP_ADMIN:
            # Clear organizations
            self.organizations = []

            # Assign permissions
            permissions_manager.assign_user_permission(self, str(self.role), _Organization.LICENSES.NONE)

        # Other user roles belong to organizations, which impose license restrictions
        # Assign permissions according to organization membership
        for organization in self.get_organizations(session, request, cascade=False):
            permissions_manager.assign_user_permission(self, str(self.role), str(organization.license))

        self.django_user.save()
