"""
********************************************************************************
* Name: model_database_base.py
* Author: nswain & ckrewson
* Created On: December 5, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import abc
import uuid


class ModelDatabaseBase(object):

    def __init__(self, app, database_id=None):
        """
        Constructor

        Args:
            app(TethysApp): TethysApp class or instance.
            database_id(str): UUID to be assigned to the database.
        """
        if not database_id:
            self.database_id = self.generate_id()
        else:
            self.database_id = database_id

        self._app = app
        self._db_url = None
        self._db_url_obj = None
        self._model_db_connection = None

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

    @abc.abstractmethod
    @property
    def model_db_connection(self):
        pass

    @abc.abstractmethod
    def initialize(self, *args, **kwargs):
        pass

    def pre_initialize(self, *args, **kwargs):
        """
        Override to perform additional initialize steps before the database and tables have been initialized.
        """
        pass

    def post_initialize(self, *args, **kwargs):
        """
        Override to perform additional initialize steps after the database and tables have been initialized.
        """
        pass

    @abc.abstractmethod
    def exists(self):
        pass

    @abc.abstractmethod
    def model_list(self):
        pass

    @classmethod
    def generate_id(cls):
        """
        Returns a UUID name for databases.
        """
        unique_name = uuid.uuid4()
        return str(unique_name).replace('-', '_')
