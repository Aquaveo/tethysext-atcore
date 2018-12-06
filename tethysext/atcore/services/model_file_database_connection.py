"""
********************************************************************************
* Name: model_file_database_connection.py
* Author: nswain & ckrewson
* Created On: December 05, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import shutil


from tethysext.atcore.services.model_database_connection_base import ModelDatabaseConnectionBase


class ModelFileDatabaseConnection(ModelDatabaseConnectionBase):
    """
    Represents a Model File Database.
    """

    def __init__(self, db_dir, db_app_namespace=None):
        """
        Constructor

        Args:
            dir_url(str): URL to model file database.
            resoureid(str): Model Resource ID
        """

        if not db_dir:
            raise ValueError("db_dir is required and must be a valid path")

        self.db_url = db_dir
        name_parts = os.path.split(self.db_url)
        self.db_name = name_parts[1]

        if db_app_namespace:
            self.db_id = self.db_name.replace(db_app_namespace + '_', '')
        else:
            self.db_id = self.db_name

    def list(self):
        """
        Returns a list of files and directories in the model database.
        """

        return os.listdir(self.db_url)

    def delete(self, name):
        """
        Deletes a file from the model database. filename can be directory or file
        """

        path = os.path.join(self.db_url, str(name))

        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isfile(path):
            shutil.rmtree(path)
        else:
            raise OSError("filename is not a directory or file. Check Name")

        return

    def add(self, filename):
        """
        Adds a file to the model database.
        """

        filepath = os.path.join(self.db_url, str(filename))

        open(filepath, 'w+').close()

        return
