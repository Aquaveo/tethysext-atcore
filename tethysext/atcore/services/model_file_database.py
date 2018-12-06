"""
********************************************************************************
* Name: model_file_database.py
* Author: nswain & ckrewson
* Created On: December 5, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import shutil

from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection
from tethysext.atcore.services.model_database_base import ModelDatabaseBase


class ModelFileDatabase(ModelDatabaseBase):
    """
    Manages the creation of file databases for models.  # noqa: E501
    """

    @property
    def model_db_connection(self):
        if self._model_db_connection is None:
            self._model_db_connection = ModelFileDatabaseConnection(self.directory, self._app.package)
        return self._model_db_connection

    @property
    def directory(self):
        """
        Returns path of resource directory
        """
        if not getattr('_directory', None):
            self._directory = os.path.join(
                self.database_root,
                '{}_{}'.format(self._app.package, self.database_id)
            )
        return self._directory

    @property
    def database_root(self):
        return self._app.get_app_workspace().path

    def duplicate(self):
        """
        makes a copy of resource directory with new uuid
        """
        src_dir = self.directory

        new_db = ModelFileDatabase(self._app)
        dst_dir = new_db.directory

        shutil.copy(src_dir, dst_dir)

        return new_db.database_id

    def exists(self):
        """
        Returns true if the model file database exists.
        """

        return os.path.isdir(self.directory)

    def list(self):
        """
        Returns a list of all models in the model file databases.
        """

        return os.listdir(self.directory)

    def delete(self):
        """
        deletes a models in the model file databases.
        """

        shutil.rmtree(self.directory)

        return str(self.directory) + "succesfully deleted"

    def initialize(self, *args, **kwargs):
        """
        Creates a new file model database if it doesn't exist.
        """

        model_file_directory = os.path.join(self.database_root, self.database_id)

        self.pre_initialize(model_file_directory)

        try:
            os.mkdir(model_file_directory)
        except OSError:
            return False

        self.post_initialize(model_file_directory)

        return self.database_id
