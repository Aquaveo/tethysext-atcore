"""
********************************************************************************
* Name: file_collection.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from tethysext.atcore.models.file_database.base import FileDatabaseBase
from tethysext.atcore.models.types import GUID


class FileCollection(FileDatabaseBase):
    """A model representing a FileCollection"""
    __tablename__ = "file_collections"

    id = Column('id', GUID, primary_key=True, default=uuid.uuid4)
    file_database_id = Column('file_database_id', GUID, ForeignKey('file_databases.id'))
    meta = Column('metadata', JSON)

    database = relationship("FileDatabase", back_populates="collections")
