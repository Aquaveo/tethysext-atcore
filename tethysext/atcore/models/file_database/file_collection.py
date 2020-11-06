"""
********************************************************************************
* Name: file_collection.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
import logging
import shutil
from typing import Generator
import uuid

from sqlalchemy import event, select, Column, ForeignKey
from sqlalchemy.types import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database.base import FileDatabaseBase
from tethysext.atcore.models.file_database.file_database import FileDatabase
from tethysext.atcore.models.types import GUID

log = logging.getLogger('tethys.' + __name__)


class FileCollection(MetaMixin, FileDatabaseBase):
    """A model representing a FileCollection"""
    __tablename__ = "file_collections"

    id = Column('id', GUID, primary_key=True, default=uuid.uuid4)
    file_database_id = Column('file_database_id', GUID, ForeignKey('file_databases.id'))
    meta = Column('metadata', MutableDict.as_mutable(JSON))

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


@event.listens_for(FileCollection, 'after_insert')
def file_collection_after_insert(mapper, connection, target):
    """SQL event listener for after insert event."""
    _file_collection_after_insert(target, connection)


def _file_collection_after_insert(target, connection):
    """A small wrapper function used so we can mock for testing."""
    file_database = _get_database_row_from_connection_and_id(connection, target.file_database_id)
    target_path = os.path.join(file_database.root_directory, str(file_database.id), str(target.id))
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    target.write_meta(path=target_path)


@event.listens_for(FileCollection, 'after_update')
def file_collection_after_update(mapper, connection, target):
    """SQL event listener for after update event."""
    _file_collection_after_update(target, connection)


def _file_collection_after_update(target, connection):
    """A small wrapper function used so we can mock for testing."""
    file_database = _get_database_row_from_connection_and_id(connection, target.file_database_id)
    target_path = os.path.join(file_database.root_directory, str(file_database.id), str(target.id))
    target.write_meta(path=target_path)


@event.listens_for(FileCollection, 'after_delete')
def file_collection_after_delete(mapper, connection, target):
    """SQL event listener for after delete event."""
    _file_collection_after_delete(target, connection)


def _file_collection_after_delete(target, connection):
    """A small wrapper function used so we can mock for testing."""
    file_database = _get_database_row_from_connection_and_id(connection, target.file_database_id)
    target_path = os.path.join(file_database.root_directory, str(file_database.id), str(target.id))
    if os.path.exists(target_path):
        try:
            shutil.rmtree(target_path)
        except OSError:
            log.warning(f'An error occurred while removing the '
                        f'file database directory: {target_path}')


def _get_database_row_from_connection_and_id(connection, database_id):
    db_table = FileDatabase.__table__
    s = select([db_table]).where(db_table.c.id == database_id)
    result = connection.execute(s)
    if result.rowcount != 1:
        raise Exception("We had some error... what should we do... this should only have one row...")
    file_database = result.first()
    return file_database
