from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.models.app_users import initialize_app_users_db
from tethysext.atcore.models.file_database import initialize_file_database_db
from tethysext.atcore.tests import TEST_DB_URL


def setup_module_for_sqlalchemy_tests():
    global transaction, connection, engine
    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    # Initialize db with staff user
    initialize_app_users_db(connection)
    initialize_file_database_db(connection)
    return engine, connection, transaction


def tear_down_module_for_sqlalchemy_tests():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class SqlAlchemyTestCase(TethysTestCase):

    def setUp(self):
        self.setup_transaction_and_session()

    def tearDown(self):
        self.tear_down_session_and_transaction()

    def setup_transaction_and_session(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

    def tear_down_session_and_transaction(self):
        self.session.close()
        self.transaction.rollback()
