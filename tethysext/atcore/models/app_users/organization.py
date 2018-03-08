import uuid

from sqlalchemy import Column, Integer, Boolean, String
from sqlalchemy.orm import relationship
from .base import AppUsersBase
from .associations import organization_resource_association, user_organization_association
from tethysext.atcore.models.guid import GUID


__all__ = ['Organization']


# Organization Types
GENERIC_ORG_TYPE = 'generic_organization_type'


class Organization(AppUsersBase):
    """
    Definition for organizations table.
    """
    __tablename__ = 'organizations'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    type = Column(String)
    active = Column(Boolean, default=True)
    storage = Column(Integer)
    access_level = Column(String)
    addons = Column(String)

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
