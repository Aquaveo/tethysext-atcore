"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from tethysext.atcore.models.file_database.base import FileDatabaseBase
from tethysext.atcore.models.types import GUID


class FileDatabase(FileDatabaseBase):
    """A model representing a FileDatabase"""
    __tablename__ = "file_databases"

    id = Column('id', GUID, primary_key=True, default=uuid.uuid4)
    root_directory = Column('root_directory', String)
    meta = Column('metadata', JSON)

    collections = relationship("FileCollection", back_populates="database")

    @property
    def path(self) -> str:
        """The root directory of the file database."""
        if not getattr(self, '_path', None):
            self._path = os.path.join(self.root_directory, str(self.id))
        return self._path

    @path.setter
    def path(self, root_dir: str) -> None:
        """
        Set the path to the root directory for the file database.

        root_dir (str): the directory to be the root directory of the file database.
        """
        self._path = os.path.join(root_dir, str(self.id))
