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
import tempfile
from filelock import FileLock

from tethysext.atcore.services.model_database_connection_base import ModelDatabaseConnectionBase


class ModelFileDatabaseConnection(ModelDatabaseConnectionBase):
    """
    Represents a Model File Database.
    """

    def __init__(self, db_dir, db_app_namespace=None, lock_timeout=5, poll_interval=0.05):
        """
        Constructor

        Args:
            db_dir(str): URL to model file database.
            db_app_namespace(str): App Namespace
        """
        if not db_dir:
            raise ValueError("db_dir is required and must be a valid path")

        self.db_dir = db_dir
        name_parts = os.path.split(self.db_dir)
        self.db_name = name_parts[1]

        if db_app_namespace:
            self.db_id = self.db_name.replace(db_app_namespace + '_', '')
        else:
            self.db_id = self.db_name

        self._lock = None
        tmp_dir = tempfile.gettempdir()
        self.lock_path = os.path.join(tmp_dir, "{}.lock".format(self.db_name))
        self.lock_timeout = lock_timeout
        self.poll_interval = poll_interval

    @property
    def lock(self):
        """
        Creates a file lock for the file database
        """
        if self._lock is None:
            self._lock = FileLock(self.lock_path, timeout=1)
        return self._lock

    def list(self):
        """
        Returns a list of files and directories in the model database.
        """
        return os.listdir(self.db_dir)

    def delete(self, filename):
        """
        Deletes a file from the model database. filename can be directory or file


        """
        path = os.path.join(self.db_dir, filename)

        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            else:
                raise ValueError("filename is not a directory or file. Check Name")

    def add(self, filepath):
        """
        Adds a file or directory (from a filepath) to the model database.

        Returns:
            str: Path to location of file within model db.
        """
        dst = os.path.join(self.db_dir, os.path.basename(filepath))

        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            if os.path.exists(dst):
                return dst
            elif os.path.isfile(filepath):
                shutil.copy(filepath, dst)
            elif os.path.isdir(filepath):
                shutil.copytree(filepath, dst)
            else:
                raise ValueError("filename is not a directory or file. Check Name")

        return dst

    def duplicate(self, ex_filename, new_filename):
        """
        Copies a file or directory to the model database.
        """
        src = os.path.join(self.db_dir, ex_filename)
        dst = os.path.join(self.db_dir, new_filename)

        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            if os.path.isfile(src):
                shutil.copy(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                raise ValueError("filename is not a directory or file. Check Name")

        return new_filename

    def move(self, ex_filename, new_filename):
        """
        Moves a file or directory to the model database.
        """
        src = os.path.join(self.db_dir, ex_filename)
        dst = os.path.join(self.db_dir, new_filename)

        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            if os.path.exists(dst):
                return dst
            elif os.path.exists(src):
                shutil.move(src, dst)
            else:
                raise ValueError("filename is not a directory or file. Check Name")

        return dst

    def bulk_delete(self, filename_list):
        """
        Bulk Deletes list of file or directories from the model database. filename can be directory or file
        """
        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            for filename in filename_list:
                path = os.path.join(self.db_dir, filename)
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    raise ValueError("filename is not a directory or file. Check Name")

    def bulk_add(self, filepath_list):
        """
        Bulk Adds list of files or directories (from a filepath) to the model database.
        """
        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            for filepath in filepath_list:
                dst = os.path.join(self.db_dir, os.path.basename(filepath))
                if os.path.exists(dst):
                    continue
                elif os.path.isfile(filepath):
                    shutil.copy(filepath, dst)
                elif os.path.isdir(filepath):
                    shutil.copytree(filepath, dst)
                else:
                    raise ValueError("filename is not a directory or file. Check Name")

    def bulk_duplicate(self, filename_list):
        """
        Bulk Copies list of files or directories to the model database.
        i.e. filename_list = [(ex_filename1, new_filename1),(ex_filename2, new_filename2)]
        """
        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            for ex_filename, new_filename in filename_list:
                src = os.path.join(self.db_dir, ex_filename)
                dst = os.path.join(self.db_dir, new_filename)
                if os.path.isfile(src):
                    shutil.copy(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    raise ValueError("filename is not a directory or file. Check Name")

    def bulk_move(self, filename_list):
        """
        Adds a file or directory to the model database.
        i.e. filename_list = [(ex_filename1, new_filename1),(ex_filename2, new_filename2)]
        """
        with self.lock.acquire(timeout=self.lock_timeout, poll_intervall=self.poll_interval):
            for ex_filename, new_filename in filename_list:
                src = os.path.join(self.db_dir, ex_filename)
                dst = os.path.join(self.db_dir, new_filename)
                if os.path.exists(dst):
                    continue
                elif os.path.exists(src):
                    shutil.move(src, dst)
                else:
                    raise ValueError("filename is not a directory or file. Check Name")
