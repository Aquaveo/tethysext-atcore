"""
********************************************************************************
* Name: model_database.py
* Author: nswain
* Created On: June 05, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


class ModelDatabaseConnection(object):
    """
    Represents a Model Database.
    """

    def __init__(self, db_url, db_app_namespace=None):
        """
        Constructor

        Args:
            db_url(str): SQLAlchemy url connection string.
            db_app_namespace(str): namespace prepended by persistent store API if applicable.
        """
        self.db_url = db_url
        self.db_url_obj = make_url(self.db_url)
        self.db_name = self.db_url_obj.database

        if db_app_namespace:
            self.db_id = self.db_name.replace(db_app_namespace + '_', '')
        else:
            self.db_id = self.db_name

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

    def get_engine(self):
        """
        Returns an SQLAlchemy engine for the model database.
        """
        return create_engine(self.db_url)

    def get_session_maker(self):
        """
        Returns an SQLAlchemy session maker for the model database.
        """
        engine = create_engine(self.db_url)
        return sessionmaker(bind=engine)

    def get_session(self):
        """
        Returns an SQLAlchemy session for the model database.
        """
        engine = create_engine(self.db_url)
        make_session = sessionmaker(bind=engine)
        return make_session()
