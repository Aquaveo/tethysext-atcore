from tethys_sdk.testing import TethysTestCase
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users.initializer import initialize_app_users_db
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.tests import APP_USER_TEST_DB


class AppUserInitializerTests(TethysTestCase):

    def setUp(self):
        # Connect to the database and create the schema within a transaction
        self.engine = create_engine(APP_USER_TEST_DB)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

    def tearDown(self):
        # Roll back the top level transaction and disconnect from the database
        self.transaction.rollback()
        self.connection.close()
        self.engine.dispose()

    def test_initialize_app_users_db_vanilla(self):
        initialize_app_users_db(self.connection)

        session = Session(self.connection)
        staff_user = session.query(AppUser). \
            filter(AppUser.username == AppUser.STAFF_USERNAME). \
            one_or_none()
        self.assertIsNotNone(staff_user)
        self.assertEqual(AppUser.ROLES.DEVELOPER, staff_user.role)
        session.close()
