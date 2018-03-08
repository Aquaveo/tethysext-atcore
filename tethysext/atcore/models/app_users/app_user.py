import uuid

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship
from tethysext.atcore.models.guid import GUID
from .associations import user_organization_association

from .base import AppUsersBase

__all__ = ['AppUser', 'UserSetting']


class AppUser(AppUsersBase):
    """
    Definition for the app_user table.
    """
    __tablename__ = 'app_users'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(String)  #: Used to map to Django user object
    role = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    organizations = relationship('Organization',
                                 secondary=user_organization_association,
                                 back_populates='users')

    settings = relationship('UserSetting', back_populates='user', cascade="delete")

    def get_django_user(self):
        """
        Get the Django user object associated with this app user object

        Returns: Django User object
        """
        from django.contrib.auth.models import User
        from django.core.exceptions import ObjectDoesNotExist
        try:
            django_user = User.objects.get(username=self.username)
        except ObjectDoesNotExist:
            return None
        return django_user
