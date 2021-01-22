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
from shutil import Error as ShutilErrors
import uuid

from sqlalchemy.orm.session import Session

from tethysext.atcore.exceptions import FileCollectionNotFoundError, FileDatabaseNotFoundError, \
    UnboundFileDatabaseError
from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database import FileCollection, FileDatabase, FileCollectionClient

log = logging.getLogger('tethys.' + __name__)


class FileDatabaseClient(MetaMixin):
    def __init__(self, session: Session, root_directory: str, file_database_id: uuid.UUID):
        """
        Use this constructor to bind the FileDatabaseClient to an existing FileDatabase. Use the new() factory method to create a new FileDatabase.

        Args:
            session (sqlalchemy.orm.Session): The session for the SQL database.
            root_directory (str): Path to the directory that contains the FileDatabase.
            file_database_id (uuid.UUID): The id of the FileDatabase.
        """
        self._database_id = file_database_id
        self._instance = None
        self._path = None
        self._session = session
        self._root_directory = root_directory
        self.__deleted = False

    @classmethod
    def new(cls, session: Session, root_directory: str, meta: dict = None) -> 'FileDatabaseClient':
        """
        Use this method to create a new FileDatabase. Use the constructor to bind to an existing FileDatabase.

        Args:
            session (sqlalchemy.orm.Session): The session for the SQL database.
            root_directory (str or Path): Directory in which the new FileDatabase will be created.
            meta (dict): The meta for the FileCollection.

        Returns:
            FileDatabaseClient: A FileDatabaseClient bound to the new FileDatabase.
        """  # noqa: E501
        meta = meta or {}
        new_file_database = FileDatabase(
            meta=meta,
        )
        session.add(new_file_database)
        session.commit()
        client = cls(session, root_directory, new_file_database.id)

        client.write_meta()

        return client

    @property
    def instance(self) -> FileDatabase:
        """Property to get the underlying instance so it can be lazy loaded."""
        if self.__deleted:
            raise UnboundFileDatabaseError('The file database has been deleted.')
        if not self._instance:
            self._instance = self._session.query(FileDatabase).get(self._database_id)
            if self._instance is None:
                raise FileDatabaseNotFoundError(f'FileDatabase with id "{str(self._database_id)}" not found.')
        return self._instance

    @property
    def root_directory(self) -> str:
        """The directory that contains the FileDatabase directory."""
        return self._root_directory

    @property
    def path(self) -> str:
        """Path to the FileDatabase directory."""
        if not getattr(self, '_path', None):
            self._path = os.path.join(self.root_directory, str(self.instance.id))
        return self._path

    def get_collection(self, collection_id: uuid.UUID) -> FileCollectionClient:
        """
        Get a FileCollectionClient owned by this FileDatabase by its collection_id

        Args:
            collection_id (uuid.UUID): The id for the file collection owned by this FileDatabase.

        Returns:
            The FileCollectionClient for the FileCollection.
        """
        file_collection_count = self._session.query(FileCollection).filter_by(
            id=collection_id, file_database_id=self.instance.id
        ).count()
        if file_collection_count != 1:
            raise FileCollectionNotFoundError(f'Collection with id "{str(collection_id)}" could not '
                                              f'be found with this database.')
        collection_client = FileCollectionClient(
            self._session, collection_id
        )
        return collection_client

    def new_collection(self, items: list = None, meta: dict = None) -> FileCollectionClient:
        """
        Create a new collection copying any files and meta data passed in.

        Args:
            items (list): A list of files or paths to be copied to the file collection.
            meta: (dict): The meta data to be stored in the FileCollection

        Returns:
            A new FileCollectionClient object for the FileCollection.
        """
        meta = meta or dict()
        items = items or list()
        new_collection = FileCollectionClient.new(self._session, self.instance.id, meta)
        for item in items:
            try:
                new_collection.add_item(item)
            except (FileNotFoundError, FileExistsError, ShutilErrors) as exc:
                new_collection.delete()
                raise exc
        return new_collection

    def delete_collection(self, collection_id: uuid.UUID) -> None:
        """
        Delete a specified FileCollection from the FileDatabase

        Args:
            collection_id (uuid.UUID): The id for the collection to be deleted.
        """
        file_collection = self.get_collection(collection_id)
        file_collection.delete()

    def export_collection(self, collection_id: uuid.UUID, target: str) -> None:
        """
        Export the collection to a target location.

        Args:
            collection_id (uuid.UUID): The id for the file collection to be exported.
            target (str): Path to the target location.
        """
        file_collection = self.get_collection(collection_id)
        file_collection.export(target)

    def duplicate_collection(self, collection_id: uuid.UUID) -> FileCollectionClient:
        """
        Duplicate a collection and add it to the FileDatabase

        Args:
            collection_id (uuid.UUID): The id for the collection to be duplicated.

        Returns:
            A FileCollectionClient for the newly duplicated FileCollect
        """
        file_collection = self.get_collection(collection_id)
        new_collection = file_collection.duplicate()
        return new_collection
