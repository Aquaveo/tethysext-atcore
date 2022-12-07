import os

from tethysext.atcore.services.file_database import FileDatabaseClient


class FileCollectionsControllerMixin:
    """Provides methods for controllers that manage on Resources with FileCollections."""

    def get_app(self):
        """
        Usually implemented by other mixins or the controller.
        """
        return None

    def delete_file_collections(self, session, resource, log):
        """
        Delete all FileCollections linked to the given resource.
        """
        # Get all file collections associated with this resource and delete them.
        app = self.get_app()
        try:
            file_database_id = app.get_custom_setting(app.FILE_DATABASE_ID_NAME)
            file_database = FileDatabaseClient(session, app.get_file_database_root(), file_database_id)

            for file_collection in resource.file_collections:
                file_database.delete_collection(file_collection.id)
        except Exception:
            log.exception(f'The file collection(s) associated with resource {resource.id} could not be deleted.')

    def get_file_collections_details(self, session, resource):
        """
        Build summary details for each FileCollection associated with the given resource.

        Args:
            session (Session): the SQLAlchemy session.
            resource (Resource): a Resource with a file_collections relationship property.

        Returns:
            list: a list of summary details table tuples, one for each FileCollection.
        """
        all_details = []
        file_collections = resource.file_collections
        app = self.get_app()

        for file_collection in file_collections:
            file_database_id = app.get_custom_setting(app.FILE_DATABASE_ID_NAME)
            file_database = FileDatabaseClient(session, app.get_file_database_root(), file_database_id)
            file_collection_client = file_database.get_collection(file_collection.id)

            file_count = 0
            total_size = 0
            # Get file count and total size
            for relative_root, dirs, files in file_collection_client.walk():
                file_count += len(files)

                for file in files:
                    file_path = os.path.join(file_collection_client.path, relative_root, file)
                    total_size += os.path.getsize(file_path)

            # Make total size human readable
            for _unit in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
                if total_size < 1024:
                    break
                total_size /= 1024.0
            total_size = f"{total_size:.2f} {_unit}"

            # Create file collection details tuple
            file_collection_details = ('File Collection Details', {
                'ID': file_collection.id,
                'File Count': file_count,
                'Total Size': total_size,
            })

            # Append meta dict
            file_collection_details[1].update(file_collection.meta)

            all_details.append(file_collection_details)

        return all_details
