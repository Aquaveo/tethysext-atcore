import datetime
import uuid

from django.utils.text import slugify
from django.utils.functional import classproperty
from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.orm import relationship, backref
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin, UserLockMixin, SerializeMixin

from .app_user import AppUsersBase
from .associations import organization_resource_association, resource_parent_child_association

__all__ = ['Resource']


class Resource(StatusMixin, AttributesMixin, UserLockMixin, SerializeMixin, AppUsersBase):
    """
    Definition for the resources table.
    """
    __tablename__ = 'app_users_resources'

    # Resource Types
    TYPE = 'resource'
    DISPLAY_TYPE_SINGULAR = 'Resource'
    DISPLAY_TYPE_PLURAL = 'Resources'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String)
    status = Column(String)
    public = Column(Boolean, default=False)
    _attributes = Column(String)
    _user_lock = Column(String)

    # Relationships
    organizations = relationship('Organization',
                                 secondary=organization_resource_association,
                                 back_populates='resources')

    children = relationship(
        'Resource',
        secondary=resource_parent_child_association,
        backref=backref('parents'),
        primaryjoin=id == resource_parent_child_association.c.parent_id,
        secondaryjoin=id == resource_parent_child_association.c.child_id,
    )

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
        'polymorphic_on': type
    }

    def __repr__(self):
        return f'<{self.__class__.__name__} name="{self.name}" id="{self.id}" locked={self.is_user_locked}>'

    @classproperty
    def SLUG(self):
        return slugify(self.DISPLAY_TYPE_PLURAL.lower()).replace("-", "_")
