import uuid

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
    license = Column(String)
    license_expires = Column(DateTime)
    created = Column(DateTime, default=func.now())
    active = Column(Boolean, default=True)
    archived = Column(Boolean, default=False)

    # Relationships
    resources = relationship('Resource',
                             secondary=organization_resource_association,
                             back_populates='organizations')
    members = relationship('AppUser',
                           secondary=user_organization_association,
                           back_populates='organizations')
    clients = relationship('Organization',
                           backref=backref('consultant', remote_side=[id]))

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
        'polymorphic_on': type
    }

    @validates('license')
    def validate_license(self, key, field):
        if key == 'license':
            if not self.LICENSE.is_valid(field):
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
