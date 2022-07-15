from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tethys_sdk.testing import TethysTestCase

from tethysext.atcore.models.app_users import AppUser, initialize_app_users_db
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests import TEST_DB_URL
from tethysext.atcore.tests.factories.django_user import UserFactory


def setup_module_for_sqlalchemy_tests():
    global transaction, connection, engine
    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    # Initialize db with staff user
    initialize_app_users_db(connection)
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
        self.session.close()  # Nested transactions seem to be deassociated on commit on 1.4

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
