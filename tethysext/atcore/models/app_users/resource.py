import datetime
import uuid

from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.orm import relationship
from tethysext.atcore.models.types.guid import GUID

from .app_user import AppUsersBase
from .associations import organization_resource_association

__all__ = ['Resource']


class Resource(AppUsersBase):
    """
    Definition for the resources table.
    """
    __tablename__ = 'resources'

    # Resource Types
    GENERIC_RESOURCE_TYPE = 'generic_resource_type'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)
    public = Column(Boolean, default=False)
    type = Column(String, default=GENERIC_RESOURCE_TYPE)

    # Relationships
    organizations = relationship('Organization',
                                 secondary=organization_resource_association,
                                 back_populates='resources')

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': GENERIC_RESOURCE_TYPE,
        'polymorphic_on': type
    }