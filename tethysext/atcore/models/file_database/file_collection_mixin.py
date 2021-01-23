import os
from typing import List, Any
import uuid

from sqlalchemy import inspect, Column, Table, ForeignKey
from sqlalchemy.orm import Session

from tethysext.atcore.models.types import GUID
from tethysext.atcore.models.app_users import AppUsersBase
from tethysext.atcore.services.file_database import FileCollectionClient, FileDatabaseClient


resource_file_collection_assoc = Table(
    'resource_file_collections_assoc',
    AppUsersBase.metadata,
    Column('id', GUID, primary_key=True, default=uuid.uuid4),
    Column('resource_id', GUID, ForeignKey('app_users_resources.id')),
    Column('file_collection_id', GUID, ForeignKey('file_collections.id'))
)


class FileCollectionMixin:
    """
    Helpful methods for managing models with a file_collections relationship. Add this mixin to model classes, replacing the file_collection property with a relationship with FileCollections, ideally using backref so FileCollections doesn't need to be modified.
    """  # noqa: E501
    # Override with relationship with FileCollections
    file_collections = []

    @classmethod
    def new(cls, file_database_client: FileDatabaseClient, files: List[str] = None, separate_collections: bool = False,
            **kwargs) -> Any:
        """
        Create a new Resource in the given file_database with given files as contents.

        Args:
            file_database_client (FileDatabaseClient): The FileDatabaseClient to use for new FileCollections.
            files (List(str)): Files to be added to the Resource FileCollections.
            separate_collections (bool): If true, each item given will be a new FileCollection
            kwargs: Other attributes of the Resource to set when creating (e.g.: name='foo', description='bar')

        Returns:
            A new Resource
        """
        session = inspect(file_database_client.instance).session
        if separate_collections:
            items_to_add = [[item] for item in files]
        else:
            items_to_add = [files]
        file_collections = [file_database_client.new_collection(item_to_add).instance for item_to_add in items_to_add]
        resource = cls(file_collections=file_collections, **kwargs)
        session.add(resource)
        session.commit()
        return resource

    def export(self, file_database_client: FileDatabaseClient, target: str) -> None:
        """
        Copy files contained in the collections to the target directory.

        Args:
            file_database_client (FileDatabaseClient): The FileDatabaseClient bound to FileDatabase that contains the FileCollections.
            target (str): The directory to export to.
        """  # noqa: E501
        session = inspect(self).session
        for collection in self.file_collections:
            file_collection_client = FileCollectionClient(session, file_database_client, collection.id)
            file_collection_client.export(os.path.join(target, str(collection.id)))

    def duplicate(self, file_database_client: FileDatabaseClient) -> Any:
        """
        Create a new Resource that includes copies of all the FileCollections of this Resource.

        Args:
            file_database_client (FileDatabaseClient): The FileDatabaseClient bound to FileDatabase that contains the FileCollections.

        Returns:
            The new Resource.
        """  # noqa: E501
        session = inspect(self).session
        collections = []
        for collection in self.file_collections:
            file_collection_client = FileCollectionClient(session, file_database_client, collection.id)
            new_collection_client = file_collection_client.duplicate()
            collections.append(new_collection_client.instance)
        resource = self.__class__(file_collections=collections)
        session.add(resource)
        session.commit()
        return resource

    def delete_collections(self, root_directory: str, session: Session = None) -> None:
        """
        Delete all associated file collections, including files on disk.

        Args:
            root_directory (str or Path): directory that contains the FileDatabase.
            session (sqlalchemy.Session): session for the SQL database. Optional. Required if Resource is not bound to a session.
        """  # noqa: E501
        s = session if session else inspect(self).session
        for collection in self.file_collections:
            database_client = FileDatabaseClient(s, root_directory, collection.database.id)
            collection_client = FileCollectionClient(s, database_client, collection.id)
            collection_client.delete()
