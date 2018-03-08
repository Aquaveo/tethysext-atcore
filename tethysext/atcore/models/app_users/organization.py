import uuid

from sqlalchemy import Column, Boolean, String
from sqlalchemy.orm import relationship
from tethysext.atcore.models.types.guid import GUID

from .associations import organization_resource_association, user_organization_association
from .base import AppUsersBase

__all__ = ['Organization']


class Organization(AppUsersBase):
    """
    Definition for organizations table.
    """
    __tablename__ = 'organizations'

    # Organization Types
    GENERIC_ORG_TYPE = 'generic_organization_type'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    type = Column(String, default=GENERIC_ORG_TYPE)
    active = Column(Boolean, default=True)

    # Relationships
    resources = relationship('Resource',
                             secondary=organization_resource_association,
                             back_populates='organizations')
    users = relationship('AppUser',
                         secondary=user_organization_association,
                         back_populates='organizations')

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': GENERIC_ORG_TYPE,
        'polymorphic_on': type
    }
