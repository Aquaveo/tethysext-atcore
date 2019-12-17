import uuid
from sqlalchemy import event
from sqlalchemy import Column, Boolean, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, backref, validates
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.services.app_users.licenses import Licenses
from .associations import organization_resource_association, user_organization_association
from .base import AppUsersBase

__all__ = ['Organization']


class Organization(AppUsersBase):
    """
    Definition for organizations table.
    """
    __tablename__ = 'app_users_organizations'

    # Organization Types
    TYPE = 'organization'
    DISPLAY_TYPE_SINGULAR = 'Organization'
    DISPLAY_TYPE_PLURAL = 'Organizations'
    LICENSES = Licenses()

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    parent_id = Column(GUID, ForeignKey('app_users_organizations.id'))
    name = Column(String)
    type = Column(String)
    created = Column(DateTime, default=func.now())
    license = Column(String, nullable=False)
    license_expires = Column(DateTime)
    active = Column(Boolean, default=True)
    archived = Column(Boolean, default=False)

    # Relationships
    resources = relationship('Resource',
                             secondary=organization_resource_association,
                             back_populates='organizations')
    members = relationship('AppUser',
                           secondary=user_organization_association,
                           back_populates='organizations')
    clients = relationship('Organization', cascade='all,delete',
                           backref=backref('consultant', remote_side=[id]))

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
        'polymorphic_on': type
    }

    @validates('license')
    def validate_license(self, key, field):
        if key == 'license':
            if not self.LICENSES.is_valid(field):
                raise ValueError('The value "{}" is not a valid license.'.format(field))

        return field

    @staticmethod
    def get_create_permission():
        """
        Get name of create permission.
        Returns:
            str: name of create permission for this type of organization.
        """
        return 'create_organizations'

    @staticmethod
    def get_edit_permission():
        """
        Get name of edit permission.
        Returns:
            str: name of edit permission for this type of organization.
        """
        return 'edit_organizations'

    @staticmethod
    def get_delete_permission():
        """
        Get name of delete permission.
        Returns:
            str: name of delete permission for this type of organization.
        """
        return 'delete_organizations'

    def get_modify_members_permission(self):
        """
        Get name of modify members permission.
        Returns:
            str: name of modify members permission for this type of organization.
        """
        return 'modify_organization_members'

    def update_member_activity(self, session, request):
        """
        Update the active status of each member.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object
            request(django.request): Django request object
        """
        for app_user in self.members:
            # Skip staff users
            if app_user.is_staff():
                continue

            app_user.update_activity(session, request)

    def can_add_client_with_license(self, session, request, license):
        """
        Determine if this organization can add a new client with the given license.
        Args:
            session(sqlalchemy.session): SQLAlchemy session object
            request(django.request): Django request object
            license: valid license.

        Returns:
            bool: True if can add client with given license, else False.
        """
        # TODO: In CityWater, use this to implement functionality of mapping part of get_owner_options_and_mapping.
        if not self.LICENSES.is_valid(license):
            raise ValueError('Invalid license given: {}.'.format(license))

        if license == self.LICENSES.STANDARD:
            return self.can_have_clients()
        elif license == self.LICENSES.ADVANCED:
            return self.can_have_clients()
        elif license == self.LICENSES.PROFESSIONAL:
            return self.can_have_clients()
        elif license == self.LICENSES.CONSULTANT:
            return self.can_have_clients()

    def can_have_clients(self):
        """
        Pass through for LICENSES.can_have_clients.
        Returns:
            bool: True if can have clients, else false.
        """
        return self.LICENSES.can_have_clients(self.license)

    def can_have_consultant(self):
        """
        Pass through for LICENSES.can_have_consultant.
        Returns:
            bool: True if can have consultant, else false.
        """
        return self.LICENSES.can_have_consultant(self.license)

    def must_have_consultant(self):
        """
        Pass through for LICENSES.must_have_consultant.
        Returns:
            bool: True if must have consultant, else false.
        """
        return self.LICENSES.must_have_consultant(self.license)

    def is_member(self, app_user):
        """
        Determine if given app_user is a member of this organization.
        Args:
            app_user(AppUser): app_user to test.

        Returns:
            bool: True when app_user is a member of this organization, else False.
        """
        for member in self.members:
            if member.id == app_user.id:
                return True

        return False


@event.listens_for(Organization, 'before_delete')
def receive_before_delete(mapper, connection, target):
    """
    Handle removal of members and resources that would be orphaned by the removal of the target organization.
    """
    sql_template = "DELETE FROM {0} WHERE {0}.{1}='{2}';"

    # Remove resources that would be orphaned.
    for resource in target.resources:
        # Resources have been disassociated from organization already
        if len(resource.organizations) < 1:
            delete_relationship = sql_template.format(
                organization_resource_association.name,
                'resource_id',
                resource.id
            )
            connection.execute(delete_relationship)

            delete_resource = sql_template.format(
                resource.__tablename__,
                'id',
                resource.id
            )
            connection.execute(delete_resource)

    # Remove users that would be orphaned
    for member in target.members:
        if len(member.organizations) < 1 and not member.is_staff():
            delete_relationship = sql_template.format(
                user_organization_association.name,
                'app_user_id',
                member.id
            )
            connection.execute(delete_relationship)

            delete_resource = sql_template.format(
                member.__tablename__,
                'id',
                member.id
            )
            connection.execute(delete_resource)
