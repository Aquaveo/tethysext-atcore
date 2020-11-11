"""
********************************************************************************
* Name: file_collection_client.py
* Author: glarsen
* Created On: November 10, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
from typing import Generator
import uuid

from sqlalchemy.orm.session import Session

from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database import FileCollection


class FileCollectionClient(MetaMixin):
    def __init__(self, session: Session, file_collection_id: uuid.UUID):
        """Init function for the FileCollectionClient"""
        self._collection_id = file_collection_id
        self._instance = None
        self._session = session

    @classmethod
    def new(cls, session: Session, file_database_id: uuid.UUID, meta: dict = None) -> 'FileCollectionClient':
        """
        Class method for creating a new instance of the FileCollectionClient class.

        Args:
            session: The session for the database.
            file_database_id (uuid.UUID): The uuid for the FileDatabase connected to this FileCollection
            meta (dict): The meta for the FileCollection
        """
        meta = meta or {}
        new_file_collection = FileCollection(
            file_database_id=file_database_id,
            meta=meta
        )
        session.add(new_file_collection)
        session.commit()
        client = cls(session, new_file_collection.id)

        client.write_meta()

        return client

    @property
    def instance(self) -> FileCollection:
        """Property to get the underlying instance so it can be lazy loaded."""
        if not self._instance:
            self._instance = self._session.query(FileCollection).get(self._collection_id)
        return self._instance

    @property
    def meta(self) -> dict:
        """Property to get the meta from the underlying instance."""
        return self.instance.meta

    @meta.setter
    def meta(self, new_meta: dict):
        """Setter to set the meta on the underlying instance."""
        self.instance.meta = new_meta

    @property
    def path(self) -> str:
        """The root directory of the file database."""
        return os.path.join(self.instance.database.root_directory, str(self.instance.database.id),
                            str(self._collection_id))

    @property
    def files(self) -> Generator[str, None, None]:
        """Generator that iterates recursively through all files (ignoring empty directories)."""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                yield os.path.relpath(os.path.join(root, file), self.path)