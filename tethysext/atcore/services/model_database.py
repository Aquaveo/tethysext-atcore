"""
********************************************************************************
* Name: model_database.py
* Author: nswain
* Created On: June 5, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import operator

from tethysext.atcore.services.model_database_connection import ModelDatabaseConnection
from tethysext.atcore.services.model_database_base import ModelDatabaseBase


class ModelDatabase(ModelDatabaseBase):
    """
    Manages the creation of databases for models and will load-balance between multiple database connections if defined by the app.  # noqa: E501
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

    def get_size(self, pretty=False):
        """
        Get the size of the ModelDatabase
        """
        engine = self.model_db_connection.get_engine()

        if not pretty:
            selection = 'SUM(pg_total_relation_size(C.oid))'
        else:
            selection = 'pg_size_pretty(SUM(pg_total_relation_size(C.oid)))'

        query = r'''
          SELECT {selection} AS "size"
          FROM pg_class C
          LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
          WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND C.relkind <> 'i'
            AND nspname !~ '^pg_toast'
            AND relname SIMILAR TO '%%epanet_\w+%%';
        '''.format(selection=selection)

        result = engine.execute(query)

        if not pretty:
            size = result.scalar()
        else:
            size = result.fetchone().size

        result.close()
        engine.dispose()

        return size

    @property
    def db_url(self):
        if self._db_url is None:
            self._db_url = str(self._app.get_persistent_store_database(self.database_id, as_url=True))
        return self._db_url

    @property
    def db_url_obj(self):
        if self._db_url_obj is None:
            self._db_url_obj = self._app.get_persistent_store_database(self.database_id, as_url=True)
        return self._db_url_obj

    @property
    def model_db_connection(self):
        if self._model_db_connection is None:
            self._model_db_connection = ModelDatabaseConnection(self.db_url, self._app.package)
        return self._model_db_connection

    def exists(self):
        """
        Returns true if the model database exists.
        """
        return self._app.persistent_store_exists(self.database_id)

    def list(self):
        """
        Returns a list names of all the model databases.
        """
        return self._app.list_persistent_store_databases()

    def get_engine(self):
        """
        Returns an SQLAlchemy engine for the model database.
        """
        return self.model_db_connection.get_engine()

    def get_session(self):
        """
        Returns an SQLAlchemy session for the model database.
        """
        return self.model_db_connection.get_session()

    def get_session_maker(self):
        """
        Returns an SQLAlchemy session maker for the model database.
        """
        return self.model_db_connection.get_session_maker()

    def initialize(self, declarative_bases=(), spatial=False):
        """
        Creates a new model database if it doesn't exist and initializes it with the data models passed in (if any).

        Args:
            declarative_bases(tuple): one or more SQLAlchemy declarative base classes used to initialize tables.
            spatial(bool): enable postgis extension on model database if True.
        """
        # Get database cluster name to create new database on.
        cluster_connection_name = self._get_cluster_connection_name_for_new_database()

        if not cluster_connection_name:
            return False

        result = self._app.create_persistent_store(
            self.database_id, connection_name=cluster_connection_name,
            spatial=spatial
        )

        if not result:
            return False

        engine = self._app.get_persistent_store_database(self.database_id)

        self.pre_initialize(engine)

        for declarative_base in declarative_bases:
            declarative_base.metadata.create_all(engine)

        self.post_initialize(engine)

        engine.dispose()

        return self.database_id

    def _get_cluster_connection_name_for_new_database(self):
        """
        Determine which database to connection to use based on a simple load balancing algorithm: (1) least number of databases and (2) least size if tied on number of database.  # noqa: E501
        Returns:
            Name of connection to use for creation of next database.
        """
        db_stats = []
        connection_names = self._app.list_persistent_store_connections()

        for connection_name in connection_names:
            count = None
            size_bytes = None
            curr_engine = self._app.get_persistent_store_connection(connection_name)

            if not curr_engine:
                continue

            # Get count of all databases: SELECT count(*) FROM pg_database;
            response = curr_engine.execute(
                'SELECT count(*) AS count '
                'FROM pg_database;'
            )

            for row in response:
                count = row.count

            # Get total cluster size (pretty): SELECT pg_catalog.pg_size_pretty(sum(pg_catalog.pg_database_size(d.datname))) AS Size FROM pg_catalog.pg_database d  # noqa: E501
            # Get total cluster size (bytes): SELECT sum(pg_catalog.pg_database_size(d.datname)) AS Size FROM pg_catalog.pg_database d  # noqa: E501
            response = curr_engine.execute(
                'SELECT sum(pg_catalog.pg_database_size(d.datname)) AS size '
                'FROM pg_catalog.pg_database d;'
            )

            for row in response:
                size_bytes = row.size

            db_stats.append((connection_name, count, size_bytes))

            curr_engine.dispose()

        # Logic for which connection here
        if not db_stats:
            return None

        db_stats.sort(key=operator.itemgetter(1, 2))

        return db_stats[0][0]
