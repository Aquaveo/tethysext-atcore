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
            db_dir(str): URL to model file database.
            db_app_namespace(str): App Namespace
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

    def delete(self, filename):
        """
        Deletes a file from the model database. filename can be directory or file
        """

        path = os.path.join(self.db_url, filename)
        try:
            if os.path.isfile(path):
                os.remove(path)
                return
            elif os.path.isdir(path):
                shutil.rmtree(path)
                return

        except OSError:
            raise OSError("filename is not a directory or file. Check Name")

        return False

    def add(self, filepath):
        """
        Adds a file or directory (from a filepath) to the model database.
        """

        try:
            if os.path.isfile(filepath):
                dst = os.path.join(self.db_url, os.path.basename(filepath))
                shutil.copy(filepath, dst)
                return dst
            elif os.path.isdir(filepath):
                dst = os.path.join(self.db_url, os.path.basename(filepath))
                shutil.copytree(filepath, dst)
                return dst

        except OSError:
            raise OSError("filename is not a directory or file. Check Name")

        return False

    def duplicate(self, ex_filename, new_filename):
        """
        Copies a file or directory to the model database.
        """

        src = os.path.join(self.db_url, ex_filename)
        dst = os.path.join(self.db_url, new_filename)

        try:
            if os.path.isfile(src):
                shutil.copy(src, dst)
                return new_filename
            elif os.path.isdir(src):
                shutil.copytree(src, dst)
                return new_filename

        except OSError:

            raise OSError("filename is not a directory or file. Check Name")

        return False

    def move(self, ex_filepath, new_filepath):
        """
        Adds a file or directory (from a filepath) to the model database.
        """

        try:
            if os.path.exists(ex_filepath):
                shutil.move(ex_filepath, new_filepath)
                return new_filepath

        except OSError:
            raise OSError("filename is not a directory or file. Check Name")

        return False

    def bulk_delete(self, filename_list):
        """
        Bulk Deletes list of file or directories from the model database. filename can be directory or file
        """

        for filename in filename_list:
            self.delete(filename)

        return

    def bulk_add(self, filepath_list):
        """
        Bulk Adds list of files or directories (from a filepath) to the model database.
        """

        for filepath in filepath_list:
            self.add(filepath)

        return

    def bulk_duplicate(self, filename_list):
        """
        Bulk Copies list of files or directories to the model database.
        i.e. filename_list = [(ex_filename1, new_filename1),(ex_filename2, new_filename2)]
        """

        for filename in filename_list:
            self.duplicate(filename[0], filename[1])

        return

    def bulk_move(self, filepath_list):
        """
        Adds a file or directory (from a filepath) to the model database.
        i.e. filepath_list = [(ex_filepath1, new_filepath1),(ex_filepath2, new_filepath2)]
        """

        for filepath in filepath_list:
            self.duplicate(filepath[0], filepath[1])

        return
