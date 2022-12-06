from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from tethys_sdk.testing import TethysTestCase

from tethysext.atcore.models.app_users import AppUser, initialize_app_users_db
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests import TEST_DB_URL
from tethysext.atcore.tests.factories.django_user import UserFactory


def setup_module_for_sqlalchemy_tests():
    global g_transaction, g_connection, g_engine, Session
    Session = sessionmaker()
    # Connect to the database and create the schema within a transaction
    g_engine = create_engine(
        TEST_DB_URL,
        pool_size=50,
        max_overflow=-1,
        connect_args={"connect_timeout": 1}
    )
    g_connection = g_engine.connect()
    g_transaction = g_connection.begin()
    # Initialize db with staff user
    initialize_app_users_db(g_engine)
    return g_engine, g_connection, g_transaction


def tear_down_module_for_sqlalchemy_tests():
    # Roll back the top level transaction and disconnect from the database
    g_transaction.rollback()
    g_connection.close()
    g_engine.dispose()


class SqlAlchemyTestCase(TethysTestCase):

    def setUp(self):
        self.setup_transaction_and_session()

    def tearDown(self):
        self.tear_down_session_and_transaction()

    def setup_transaction_and_session(self):
        self.connection = g_engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection)
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if not self.nested.is_active:
                self.nested = self.connection.begin_nested()

    def tear_down_session_and_transaction(self):
        self.session.close()
        self.transaction.rollback()
        self.connection.close()

    def get_user(self, is_staff=False, return_app_user=False, user_role=Roles.ORG_USER):
        """Make a Django User and/or associated AppUser instance."""
        django_user = UserFactory()
        django_user.is_staff = is_staff
        django_user.is_superuser = is_staff
        django_user.save()

        app_user = AppUser(
            username=django_user.username,
            role=Roles.DEVELOPER if is_staff else user_role,
            is_active=True,
        )
        self.session.add(app_user)
        self.session.commit()

        return app_user if return_app_user else django_user
