"""
********************************************************************************
* Name: file_collection.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.types import GUID

if TYPE_CHECKING:
    from tethysext.atcore.models.file_database.file_database import FileDatabase


class FileCollection(AppUsersBase):
    """A model representing a FileCollection"""
    __tablename__ = "file_collections"

    id: Mapped[uuid.UUID] = mapped_column('id', GUID, primary_key=True, default=uuid.uuid4)
    file_database_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        'file_database_id', GUID, ForeignKey('file_databases.id'),
    )
    meta: Mapped[Optional[dict]] = mapped_column('metadata', JSON)

    database: Mapped[Optional["FileDatabase"]] = relationship("FileDatabase", back_populates="collections")
