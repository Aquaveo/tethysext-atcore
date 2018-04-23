"""
********************************************************************************
* Name: user_setting.py
* Author: nswain
* Created On: April 18, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import uuid
from sqlalchemy import Column, ForeignKey, String
from tethysext.atcore.models.types.guid import GUID
from sqlalchemy.orm import relationship
from .base import AppUsersBase


class UserSetting(AppUsersBase):
    """
    SQLAlchemy interface for user_settings table.
    """
    __tablename__ = "user_settings"

    # Primary and Foreign Keys
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey('app_users.id'))

    # Properties
    resource_id = Column(GUID, nullable=True, default=None)
    secondary_id = Column(String, nullable=True, default=None)
    page = Column(String, nullable=True, default=None)
    key = Column(String)
    value = Column(String)

    # Relationship
    user = relationship('AppUser', back_populates='settings')
