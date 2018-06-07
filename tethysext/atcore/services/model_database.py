"""
********************************************************************************
* Name: model_database.py
* Author: nswain
* Created On: June 5, 2018
* Copyright: (c) Aquaveo 2018
* License: 
********************************************************************************
"""
import uuid
import operator

from tethysext.atcore.services.model_database_connection import ModelDatabaseConnection


class ModelDatabase(object):
    """
    Represents a Model Database. Manages the creation of model databases and will load-balance between multiple database connections if defined by the app.
    """

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

    def get_size(self, pretty=False):
        """
        Get the size of the ModelDatabase
        """
        engine = self.model_db_connection.get_engine()

        if not pretty:
            selection = 'SUM(pg_total_relation_size(C.oid))'
        else:
            selection = 'pg_size_pretty(SUM(pg_total_relation_size(C.oid)))'
        query = '''
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

    def initialize(self, declarative_bases=()):
        """
        Creates a new model database if it doesn't exist and initializes it with the data models passed in (if any).

        Args:
            declarative_bases(tuple): one or more SQLAlchemy declarative base classes used to initialize tables.
        """
        # Get database cluster name to create new database on.
        cluster_connection_name = self._get_cluster_connection_name_for_new_database()

        result = self._app.create_persistent_store(
            self.database_id, connection_name=cluster_connection_name,
            spatial=True
        )

        if not result:
            return False

        engine = self._app.get_persistent_store_database(self.database_id)

        self.pre_initialize(engine)

        for declarative_base in declarative_bases:
            declarative_base.metadata.create_all(engine)

        self.post_initialize(engine)

        return self.database_id

    def _get_cluster_connection_name_for_new_database(self):
        """
        Determine which database to connection to use based on a simple load balancing algorithm: (1) least number of databases and (2) least size if tied on number of database.
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

            # Get total cluster size (pretty): SELECT pg_catalog.pg_size_pretty(sum(pg_catalog.pg_database_size(d.datname))) AS Size FROM pg_catalog.pg_database d
            # Get total cluster size (bytes): SELECT sum(pg_catalog.pg_database_size(d.datname)) AS Size FROM pg_catalog.pg_database d
            response = curr_engine.execute(
                'SELECT sum(pg_catalog.pg_database_size(d.datname)) AS size '
                'FROM pg_catalog.pg_database d;'
            )

            for row in response:
                size_bytes = row.size

            db_stats.append((connection_name, count, size_bytes))

        # Logic for which connection here
        if not db_stats:
            return None

        db_stats.sort(key=operator.itemgetter(1, 2))

        return db_stats[0][0]

    def pre_initialize(self, engine):
        """
        Override to perform additional initialize steps before the database and tables have been initialized.
        """
        pass

    def post_initialize(self, engine):
        """
        Override to perform additional initialize steps after the database and tables have been initialized.
        """
        pass

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

    @classmethod
    def generate_id(cls):
        """
        Returns a UUID name for databases.
        """
        unique_name = uuid.uuid4()
        return str(unique_name).replace('-', '_')
