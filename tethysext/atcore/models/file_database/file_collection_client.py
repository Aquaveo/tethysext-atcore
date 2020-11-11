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

from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database import FileCollection


class FileCollectionClient(MetaMixin):
    def __init__(self, session, file_collection_id: uuid.UUID):
        self._collection_id = file_collection_id
        self._instance = None
        self._session = session

    @classmethod
    def new(cls, session, file_database_id, meta=dict):
        meta = meta or {}
        new_file_collection = FileCollection(
            file_database_id=file_database_id,
            mata=meta
        )
        session.add(new_file_collection)
        session.commit()
        client = cls(session, new_file_collection.id)

        client.write_meta()

        return client

    @property
    def instance(self) -> FileCollection:
        if not self._instance:
            self._instance = self._session.query(FileCollection).get(self._collection_id)
        return self._instance

    @property
    def path(self) -> str:
        """The root directory of the file database."""
        return os.path.join(self._instance.database.path, str(self._collection_id))

    @property
    def files(self) -> Generator[str, None, None]:
        """Generator that iterates recursively through all files (ignoring empty directories)."""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                yield os.path.relpath(os.path.join(root, file), self.path)
