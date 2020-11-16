"""
********************************************************************************
* Name: file_collection_client.py
* Author: glarsen
* Created On: November 10, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from contextlib import contextmanager
import os
import shutil
from typing import Generator
import uuid

from sqlalchemy.orm.session import Session

from tethysext.atcore.exceptions import FileCollectionNotFoundError, UnboundFileCollectionError, \
    FileCollectionItemNotFoundError, FileCollectionItemAlreadyExistsError
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
            raise UnboundFileCollectionError('The collection has been deleted.')
        if not self._instance:
            self._instance = self._session.query(FileCollection).get(self._collection_id)
            if self._instance is None:
                raise FileCollectionNotFoundError(f'FileCollection with id "{str(self._collection_id)}" not found.')
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
                os.makedirs(target)
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
        raise NotImplementedError("IMPLEMENT THIS FUNCTION")
