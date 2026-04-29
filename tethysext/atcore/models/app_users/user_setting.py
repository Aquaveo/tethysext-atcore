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
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, String
from tethysext.atcore.models.types.guid import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import AppUsersBase
from tethysext.atcore.mixins import AttributesMixin

if TYPE_CHECKING:
    from .app_user import AppUser


class UserSetting(AttributesMixin, AppUsersBase):
    """
    SQLAlchemy interface for user_settings table.
    """
    __tablename__ = "app_users_user_settings"

    # Primary and Foreign Keys
    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey('app_users_app_users.id'))

    # Properties
    _attributes: Mapped[Optional[str]] = mapped_column(String, default=json.dumps({}))
    key: Mapped[Optional[str]] = mapped_column(String)
    value: Mapped[Optional[str]] = mapped_column(String)

    # Relationship
    user: Mapped[Optional["AppUser"]] = relationship('AppUser', back_populates='settings')
