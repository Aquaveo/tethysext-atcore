"""
********************************************************************************
* Name: file_database_client.py
* Author: glarsen
* Created On: November 10, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
import logging
import uuid

from sqlalchemy.orm.session import Session

from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database import FileDatabase, FileCollectionClient

log = logging.getLogger('tethys.' + __name__)


class FileDatabaseClient(MetaMixin):
    def __init__(self, session: Session, file_database_id: uuid.UUID):
        """Init function for the FileDatabaseClient"""
        self._database_id = file_database_id
        self._instance = None
        self._session = session
        self._path = None

    @classmethod
    def new(cls, session: Session, root_directory: str, meta: dict = None) -> 'FileDatabaseClient':
        """
        Class method for creating a new instance of the FileCollectionClient class.

        Args:
            session: The session for the database.
            root_directory (str): Directory for the files for this FileDatabase
            meta (dict): The meta for the FileCollection
        """
        meta = meta or {}
        new_file_database = FileDatabase(
            root_directory=root_directory,
            meta=meta,
        )
        session.add(new_file_database)
        session.commit()
        client = cls(session, new_file_database.id)

        client.write_meta()

        return client

    @property
    def instance(self) -> FileDatabase:
        """Property to get the underlying instance so it can be lazy loaded."""
        if not self._instance:
            self._instance = self._session.query(FileDatabase).get(self._database_id)
        return self._instance

    @property
    def path(self) -> str:
        """The root directory of the file database."""
        if not getattr(self, '_path', None):
            self._path = os.path.join(self.instance.root_directory, str(self.instance.id))
        return self._path

    @path.setter
    def path(self, root_dir: str) -> None:
        """
        Set the path to the root directory for the file database.

        root_dir (str): the directory to be the root directory of the file database.
        """
        self._path = os.path.join(root_dir, str(self.instance.id))

    def get_collection(self, collection_id: uuid.UUID) -> FileCollectionClient:
        """
        Get a FileCollectionClient owned by this FileDatabase by its collection_id

        Args:
            collection_id (uuid.UUID): The id for the file collection owned by this FileDatabase.

        Returns:
            The FileCollectionClient for the FileCollection.
        """
        raise NotImplementedError("WRITE THIS FUNCTION")

    def new_collection(self, items: list = None, meta: dict = None) -> FileCollectionClient:
        """
        Create a new collection copying any files and meta data passed in.

        Args:
            items (list): A list of files or paths to be copied to the file collection.
            meta: (dict): The meta data to be stored in the FileCollection

        Returns:
            A new FileCollectionClient object for the FileCollection.
        """
        raise NotImplementedError("WRITE THIS FUNCTION")

    def delete_collection(self, collection_id: uuid.UUID) -> None:
        """
        Delete a specified FileCollection from the FileDatabase

        Args:
            collection_id (uuid.UUID): The id for the collection to be deleted.
        """
        raise NotImplementedError("WRITE THIS FUNCTION")

    def export_collection(self, collection_id: uuid.UUID, target: str) -> None:
        """
        Export the collection to a target location.

        Args:
            collection_id (uuid.UUID): The id for the file collection to be exported.
            target (str): Path to the target location.
        """
        raise NotImplementedError("WRITE THIS FUNCTION")

    def duplicate_collection(self, collection_id: uuid.UUID) -> FileCollectionClient:
        """
        Duplicate a collection and add it to the FileDatabase

        Args:
            collection_id (uuid.UUID): The id for the collection to be duplicated.

        Returns:
            A FileCollectionClient for the newly duplicated FileCollect
        """
        raise NotImplementedError("WRITE THIS FUNCTION")
