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

    def get_name(self):
        """
        DB name getter (e.g.: my_app_02893760_1f1e_43a2_8578_b10fc829c15f).
        """
        return self.model_db_connection.get_name()

    def get_id(self):
        """
        DB id getter (e.g.: 02893760_1f1e_43a2_8578_b10fc829c15f).
        """
        return self.model_db_connection.get_id()

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
        if not getattr(self, '_directory', None):
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

        shutil.copytree(src_dir, dst_dir)

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

        return os.listdir(self.database_root)

    def delete(self):
        """
        deletes a models in the model file databases.
        """

        shutil.rmtree(self.directory)

    def initialize(self, *args, **kwargs):
        """
        Creates a new file model database if it doesn't exist.
        """

        self.pre_initialize(self.directory)

        try:
            os.mkdir(self.directory)
        except OSError:
            return False

        self.post_initialize(self.directory)

        return self.database_id
