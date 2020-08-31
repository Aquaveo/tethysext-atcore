"""
********************************************************************************
* Name: user_setting.py
* Author: nswain
* Created On: April 18, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import uuid
import json
from sqlalchemy import Column, ForeignKey, String
from tethysext.atcore.models.types.guid import GUID
from sqlalchemy.orm import relationship
from .base import AppUsersBase
from tethysext.atcore.mixins import AttributesMixin


class UserSetting(AttributesMixin, AppUsersBase):
    """
    SQLAlchemy interface for user_settings table.
    """
    __tablename__ = "app_users_user_settings"

    # Primary and Foreign Keys
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey('app_users_app_users.id'))

    # Properties
    _attributes = Column(String, default=json.dumps({}))
    key = Column(String)
    value = Column(String)

    # Relationship
    user = relationship('AppUser', back_populates='settings')
