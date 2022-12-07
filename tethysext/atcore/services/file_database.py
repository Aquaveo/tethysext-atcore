"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: November 10, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
import logging
import shutil
from contextlib import contextmanager
from shutil import Error as ShutilErrors
import uuid
from typing import Generator

from sqlalchemy.orm import Session

from tethysext.atcore.exceptions import FileCollectionNotFoundError, FileDatabaseNotFoundError, \
    UnboundFileDatabaseError, UnboundFileCollectionError, FileCollectionItemNotFoundError, \
    FileCollectionItemAlreadyExistsError
from tethysext.atcore.mixins.meta_mixin import MetaMixin
from tethysext.atcore.models.file_database import FileCollection, FileDatabase

__all__ = ['FileDatabaseClient', 'FileCollectionClient']

log = logging.getLogger('tethys.' + __name__)


class FileDatabaseClient(MetaMixin):
    def __init__(self, session: Session, root_directory: str, file_database_id: uuid.UUID):
        """
        Use this constructor to bind the FileDatabaseClient to an existing FileDatabase. Use the new() factory method to create a new FileDatabase.

        Args:
            session (sqlalchemy.orm.Session): The session for the SQL database.
            root_directory (str): Path to the directory that contains the FileDatabase.
            file_database_id (uuid.UUID): The id of the FileDatabase.
        """  # noqa: E501
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

    def get_collection(self, collection_id: uuid.UUID) -> 'FileCollectionClient':
        """
        Get a FileCollectionClient owned by this FileDatabase by its collection_id

        Args:
            collection_id (uuid.UUID): The id for the file collection owned by this FileDatabase.

        Returns:
            The FileCollectionClient for the FileCollection.
        """
        file_collection_count = self._session.query(FileCollection)\
            .filter_by(id=collection_id, file_database_id=self.instance.id)\
            .count()
        if file_collection_count != 1:
            raise FileCollectionNotFoundError(f'Collection with id "{str(collection_id)}" could not '
                                              f'be found with this database.')
        collection_client = FileCollectionClient(
            self._session, self, collection_id
        )
        return collection_client

    def new_collection(self, items: list = None, meta: dict = None) -> 'FileCollectionClient':
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
        new_collection = FileCollectionClient.new(self._session, self, meta)
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

    def duplicate_collection(self, collection_id: uuid.UUID) -> 'FileCollectionClient':
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


class FileCollectionClient(MetaMixin):
    def __init__(self, session: Session, file_database_client: FileDatabaseClient, file_collection_id: uuid.UUID):
        """
        Use this constructor to bind the FileCollectionClient to an existing FileCollection. Use the new() factory method to create a new FileCollection.

        Args:
            session (sqlalchemy.orm.Session): The session for the SQL database.
            file_database_client (FileDatabaseClient): A FileDatabaseClient bound to the FileDatabase containing the FileCollection.
            file_collection_id (uuid.UUID): The id of the FileCollection.
        """  # noqa: E501
        self._collection_id = file_collection_id
        self._file_database_client = file_database_client
        self._instance = None
        self._session = session
        self.__deleted = False

    @classmethod
    def new(cls, session: Session, file_database_client: FileDatabaseClient, meta: dict = None) \
            -> 'FileCollectionClient':
        """
        Use this method to create a new FileCollection. Use the constructor to bind to an existing FileCollection.

        Args:
            session (sqlalchemy.orm.Session): The session for the SQL database.
            file_database_client (FileDatabaseClient): A FileDatabaseClient bound to the FileDatabase in which you would like the new FileCollection to be created.
            meta (dict): The meta for the FileCollection

        Returns:
            A client to a newly generated FileCollection.
        """  # noqa: E501
        meta = meta or {}
        new_file_collection = FileCollection(
            file_database_id=file_database_client.instance.id,
            meta=meta
        )
        session.add(new_file_collection)
        session.commit()
        client = cls(session, file_database_client, new_file_collection.id)

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
            raise UnboundFileCollectionError('The collection has been deleted.')
        if not self._instance:
            self._instance = self._session.query(FileCollection).get(self._collection_id)
            if self._instance is None:
                raise FileCollectionNotFoundError(f'FileCollection with id "{str(self._collection_id)}" not found.')
        return self._instance

    @property
    def file_database_client(self) -> FileDatabaseClient:
        """FileDatabaseClient bound to the FileDatabase containing the FileCollection."""
        return self._file_database_client

    @property
    def path(self) -> str:
        """Path to the FileCollection directory."""
        return os.path.join(self.file_database_client.root_directory, str(self.instance.database.id),
                            str(self._collection_id))

    @property
    def files(self) -> Generator[str, None, None]:
        """
        Generator that iterates recursively through all files (ignoring empty directories).

        Returns:
            Generate giving a list of files in the FileCollection
        """
        for root, _, files in os.walk(self.path):
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
            file_database_client=self.file_database_client,
            meta=self.instance.meta,
        )
        self.export(duplicated_client.path)
        return duplicated_client

    def add_item(self, item: str, move: bool = False) -> None:
        """
        Add an item to the file collection.

        Args:
            item: A path to the item to be added.
            move: Move the file if True, otherwise just copy.
        """
        if not os.path.exists(item):
            raise FileNotFoundError('Item to be added does not exist.')

        if self.path in item:
            raise FileExistsError('Item to be added must not already be contained in the FileCollection.')

        if move:
            shutil.move(item, self.path)
        else:
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(self.path, os.path.split(item)[-1]))
            else:
                shutil.copy(item, self.path)

    def delete_item(self, item: str):
        """
        Delete an item from the file collection.

        Args:
            item (str): Path to the item to be deleted, relative to the collection.
        """
        item_path = os.path.join(self.path, item)
        if not os.path.exists(item_path):
            raise FileCollectionItemNotFoundError(f'"{item}" not found in this collection.')

        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

    def export_item(self, item: str, target: str):
        """
        Export an item from the collection to a new location.

        Args:
            item (str): Path to the item to be exported, relative to the collection.
            target (str): Path to the export location.
        """
        item_full_path = os.path.join(self.path, item)
        if not os.path.exists(item_full_path):
            raise FileCollectionItemNotFoundError(f'"{item}" not found in this collection.')

        item_is_dir = os.path.isdir(item_full_path)

        if item_is_dir:
            if os.path.exists(target):
                raise IsADirectoryError(f'The directory to you are trying to export to already exists. {target}')
            shutil.copytree(item_full_path, target)
        else:
            if os.path.exists(target):
                if os.path.isdir(target):
                    # copy file to directory
                    shutil.copy(item_full_path, target)
                else:
                    raise FileExistsError(f'Target already exists: "{target}"')
            else:
                if os.path.splitext(target)[-1] == '':
                    if not os.path.exists(target):
                        os.makedirs(target)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy(item_full_path, target)

    def duplicate_item(self, item, new_item):
        """
        Duplicate an item in the collection.

        Args:
            item (str): Path to the item to duplicate, relative to the collection.
            new_item (str): Path to the new item, relative to the collection.
        """
        try:
            self.export_item(item, os.path.join(self.path, new_item))
        except (FileExistsError, IsADirectoryError):
            raise FileCollectionItemAlreadyExistsError('Collection duplication target already exists.')

    @contextmanager
    def open_file(self, file, *args, **kwargs):
        """
        Open a file in the collection for reading/writing.

        Args:
            file: The file to be opened, relative to the collection.
            args, kwargs: Additional arguments passed to open function.

        Returns:
            A handle to the file that has been opened.
        """
        item_path = os.path.join(self.path, file)
        if not os.path.exists(item_path):
            raise FileCollectionItemNotFoundError(f'"{file}" not found in this collection.')

        f = open(item_path, *args, **kwargs)
        try:
            yield f
        finally:
            f.close()

    def walk(self):
        """Walk through the files, and directories of the collection recursively."""
        for root, dirs, files in os.walk(self.path):
            relative_root = os.path.relpath(root, start=self.path)
            yield relative_root, dirs, files
