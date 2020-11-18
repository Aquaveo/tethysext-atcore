"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: October 30, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.types import GUID


class FileDatabase(AppUsersBase):
    """A model representing a FileDatabase"""
    __tablename__ = "file_databases"

    id = Column('id', GUID, primary_key=True, default=uuid.uuid4)
    root_directory = Column('root_directory', String)
    meta = Column('metadata', JSON)

    collections = relationship("FileCollection", back_populates="database")
