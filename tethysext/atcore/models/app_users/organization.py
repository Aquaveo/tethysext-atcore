import uuid
from sqlalchemy import event
from sqlalchemy import Column, Boolean, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, backref, validates, sessionmaker
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.services.app_users.licenses import Licenses
from .associations import organization_resource_association, user_organization_association
from .base import AppUsersBase

__all__ = ['Organization']


class Organization(AppUsersBase):
    """
    Definition for organizations table.
    """
    __tablename__ = 'organizations'

    # Organization Types
    TYPE = 'organization'
    DISPLAY_TYPE_SINGULAR = 'Organization'
    DISPLAY_TYPE_PLURAL = 'Organizations'
    LICENSES = Licenses()

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    parent_id = Column(GUID, ForeignKey('organizations.id'))
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
    clients = relationship('Organization', cascade="all,delete",
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

    def get_modify_permission(self):
        """
        Get name of modify permission.
        Returns:
            str: name of modify permission for this type of organization.
        """
        return 'modify_organizations'

    def get_modify_members_permission(self):
        """
        Get name of modify members permission.
        Returns:
            str: name of modify members permission for this type of organization.
        """
        return 'modify_organization_members'


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
        if len(member.organizations) < 1:
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
