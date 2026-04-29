import datetime
import uuid
from typing import TYPE_CHECKING, Optional

from django.utils.text import slugify
from django.utils.functional import classproperty
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin, UserLockMixin, SerializeMixin

from .app_user import AppUsersBase
from .associations import organization_resource_association, resource_parent_child_association

if TYPE_CHECKING:
    from .organization import Organization
    from .resource_workflow import ResourceWorkflow

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

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    type: Mapped[Optional[str]] = mapped_column(String)
    date_created: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String)
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    _attributes: Mapped[Optional[str]] = mapped_column(String)
    _user_lock: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    organizations: Mapped[list["Organization"]] = relationship(
        'Organization',
        secondary=organization_resource_association,
        back_populates='resources',
    )

    children: Mapped[list["Resource"]] = relationship(
        'Resource',
        secondary=resource_parent_child_association,
        back_populates='parents',
        primaryjoin=id == resource_parent_child_association.c.parent_id,
        secondaryjoin=id == resource_parent_child_association.c.child_id,
    )

    parents: Mapped[list["Resource"]] = relationship(
        'Resource',
        secondary=resource_parent_child_association,
        back_populates='children',
        primaryjoin=id == resource_parent_child_association.c.child_id,
        secondaryjoin=id == resource_parent_child_association.c.parent_id,
    )

    workflows: Mapped[list["ResourceWorkflow"]] = relationship(
        'ResourceWorkflow',
        back_populates='resource',
        cascade='all,delete',
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

    def serialize_base_fields(self, d: dict) -> dict:
        """Hook for ATCore base classes to add their custom fields to serialization.

        Args:
            d: Base serialized Resource dictionary.

        Returns:
            Serialized Resource dictionary.
        """
        d.update({
            'created_by': self.created_by,
            'date_created': self.date_created,
            'description': self.description,
            'display_type_plural': self.DISPLAY_TYPE_PLURAL,
            'display_type_singular': self.DISPLAY_TYPE_SINGULAR,
            'organizations': [{
                'id': org.id,
                'name': org.name
            } for org in self.organizations],
            'public': self.public,
            'slug': self.SLUG,
        })
        return d
