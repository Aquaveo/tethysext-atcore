"""
********************************************************************************
* Name: file_collection_client.py
* Author: glarsen
* Created On: November 10, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
import shutil
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
        self.__deleted = False

    @classmethod
    def new(cls, session: Session, file_database_id: uuid.UUID, meta: dict = None) -> 'FileCollectionClient':
        """
        Class method for creating a new instance of the FileCollectionClient class.

        Args:
            session: The session for the database.
            file_database_id (uuid.UUID): The uuid for the FileDatabase connected to this FileCollection
            meta (dict): The meta for the FileCollection

        Returns:
            A client to a newly generated FileCollection.
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
        """
        Property to get the underlying instance so it can be lazy loaded.

        Returns:
            The underlying FileCollection instance.

        Raises:
            Exception: If the the instance has been deleted.
        """
        if self.__deleted:
            raise Exception('The collection has been deleted.')
        if not self._instance:
            self._instance = self._session.query(FileCollection).get(self._collection_id)
        return self._instance

    @property
    def path(self) -> str:
        """
        The root directory of the file database.

        Returns:
            The path to the FileCollection
        """
        return os.path.join(self.instance.database.root_directory, str(self.instance.database.id),
                            str(self._collection_id))

    @property
    def files(self) -> Generator[str, None, None]:
        """
        Generator that iterates recursively through all files (ignoring empty directories).

        Returns:
            Generate giving a list of files in the FileCollection
        """
        for root, dirs, files in os.walk(self.path):
            for file in files:
                yield os.path.relpath(os.path.join(root, file), self.path)

    def delete(self):
        """Delete this CollectionInstance"""
        shutil.rmtree(self.path)
        self._session.delete(self.instance)
        self._session.commit()
        self.__deleted = True

    def export(self, target):
        """
        Copy the FileCollection to the target.

        Args:
            target (str): location of the newly exported FileCollection.
        """
        for file in self.files:
            src_file = os.path.join(self.path, file)
            dst_file = os.path.join(target, file)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copyfile(src_file, dst_file)

    def duplicate(self):
        """
        Duplicate collection with a new ID and associate it with the current FileDatabase

        Returns:
            A client for the newly duplicated FileCollection
        """
        duplicated_client = FileCollectionClient.new(
            session=self._session,
            file_database_id=self.instance.file_database_id,
            meta=self.instance.meta,
        )
        self.export(duplicated_client.path)
        return duplicated_client
