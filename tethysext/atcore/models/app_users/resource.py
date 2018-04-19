import datetime
import uuid
import json

from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.orm import relationship
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.mixins import StatusMixin

from .app_user import AppUsersBase
from .associations import organization_resource_association

__all__ = ['Resource']


class Resource(StatusMixin, AppUsersBase):
    """
    Definition for the resources table.
    """
    __tablename__ = 'resources'

    # Resource Types
    TYPE = 'resource'
    DISPLAY_TYPE_SINGULAR = 'Resource'
    DISPLAY_TYPE_PLURAL = 'Resources'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    location = Column(String)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String)
    status = Column(String)
    public = Column(Boolean, default=False)
    _attributes = Column(String)

    # Relationships
    organizations = relationship('Organization',
                                 secondary=organization_resource_association,
                                 back_populates='resources')

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
        'polymorphic_on': type
    }

    @property
    def attributes(self):
        if not self._attributes:
            self._attributes = json.dumps({})
        return json.loads(self._attributes)

    @attributes.setter
    def attributes(self, value):
        self._attributes = json.dumps(value)

    def get_attribute(self, key):
        """
        Get value of a specific attribute.
        Args:
            key(str): key of attribute.

        Returns:
            varies: value of attribute.
        """
        if key not in self.attributes:
            return None

        return self.attributes[key]

    def set_attribute(self, key, value):
        """
        Set value of a specific attribute.
        Args:
            key(str): key of attribute
            value: value of attribute
        """
        attrs = self.attributes
        attrs[key] = value
        self.attributes = attrs
