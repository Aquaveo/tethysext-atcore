"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
import os
import shutil
import uuid

from sqlalchemy import event, Column, String
from sqlalchemy.types import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database.base import FileDatabaseBase
from tethysext.atcore.models.types import GUID

log = logging.getLogger('tethys.' + __name__)


class FileDatabase(MetaMixin, FileDatabaseBase):
    """A model representing a FileDatabase"""
    __tablename__ = "file_databases"

    id = Column('id', GUID, primary_key=True, default=uuid.uuid4)
    root_directory = Column('root_directory', String)
    meta = Column('metadata', MutableDict.as_mutable(JSON))

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


@event.listens_for(FileDatabase, 'after_insert')
def file_database_after_insert(mapper, connection, target):
    """SQL event listener for after insert event."""
    _file_database_after_insert(target)


def _file_database_after_insert(target):
    """A small wrapper function used so we can mock for testing."""
    if not os.path.exists(target.path):
        os.makedirs(target.path)
    target.write_meta()


@event.listens_for(FileDatabase, 'before_update')
def file_database_after_update(mapper, connection, target):
    """SQL event listener for after update event."""
    _file_database_after_update(target)


def _file_database_after_update(target):
    """A small wrapper function used so we can mock for testing."""
    target.write_meta()


@event.listens_for(FileDatabase, 'after_delete')
def file_database_after_delete(mapper, connection, target):
    """SQL event listener for after delete event."""
    _file_database_after_delete(target)


def _file_database_after_delete(target):
    """A small wrapper function used so we can mock for testing."""
    if os.path.exists(target.path):
        try:
            shutil.rmtree(target.path)
        except OSError:
            log.warning(f'An error occurred while removing the '
                        f'file database directory: {target.path}')
