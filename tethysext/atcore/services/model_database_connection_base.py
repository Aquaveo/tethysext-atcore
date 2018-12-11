"""
********************************************************************************
* Name: model_file_database_connection_base.py
* Author: nswain
* Created On: June 05, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


class ModelDatabaseConnectionBase(object):
    """
    Represents a Model Database.
    """

    db_name = None
    db_url = None
    db_id = None

    def get_id(self):
        """
        DB id getter.
        """
        return self.db_id

    def get_name(self):
        """
        DB name getter.
        """
        return self.db_name
