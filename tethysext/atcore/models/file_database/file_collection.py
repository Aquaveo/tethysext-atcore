"""
********************************************************************************
* Name: file_collection.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
from typing import Generator
import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from tethysext.atcore.models.file_database.base import FileDatabaseBase
from tethysext.atcore.models.file_database.meta_mixin import MetaMixin
from tethysext.atcore.models.types import GUID


class FileCollection(MetaMixin, FileDatabaseBase):
    """A model representing a FileCollection"""
    __tablename__ = "file_collections"

    id = Column('id', GUID, primary_key=True, default=uuid.uuid4)
    file_database_id = Column('file_database_id', GUID, ForeignKey('file_databases.id'))

    database = relationship("FileDatabase", back_populates="collections")

    @property
    def path(self) -> str:
        """The root directory of the file database."""
        return os.path.join(self.database.path, str(self.id))

    @property
    def files(self) -> Generator[str, None, None]:
        """Generator that iterates recursively through all files (ignoring empty directories)."""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                yield os.path.relpath(os.path.join(root, file), self.path)
