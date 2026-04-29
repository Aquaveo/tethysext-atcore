"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import uuid
from typing import Optional

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.file_database.file_collection import FileCollection
from tethysext.atcore.models.types import GUID


class FileDatabase(AppUsersBase):
    """A model representing a FileDatabase"""
    __tablename__ = "file_databases"

    id: Mapped[uuid.UUID] = mapped_column('id', GUID, primary_key=True, default=uuid.uuid4)
    meta: Mapped[Optional[dict]] = mapped_column('metadata', JSON)

    collections: Mapped[list[FileCollection]] = relationship("FileCollection", back_populates="database")
