from tethys_sdk.testing import TethysTestCase
from django.contrib.auth.models import User
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users import AppUsersBase, AppUser


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine('postgresql://tethys_super:pass@localhost:5435/appusertests')
    connection = engine.connect()
    transaction = connection.begin()
    AppUsersBase.metadata.create_all(connection)

    # If you want to insert fixtures to the DB, do it here


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class AppUserTests(TethysTestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.username = "test_user"
        self.role = "tester"
        self.is_active = True

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_get_django_user_existing(self):
        created_app_user = AppUser(
            username=self.username,
            role=self.role,
            is_active=self.is_active,
        )

        created_django_user = User.objects.create_user(
            username=self.username,
            password="pass",
        )

        self.session.add(created_app_user)
        self.session.commit()

        all_user_count = self.session.query(AppUser).count()
        all_users = self.session.query(AppUser).all()

        self.assertEqual(all_user_count, 1)
        for user in all_users:
            returned_django_user = user.get_django_user()
            self.assertEquals(created_django_user, returned_django_user)

    def test_get_django_user_non_existing(self):
        created_app_user = AppUser(
            username=self.username,
            role=self.role,
            is_active=self.is_active,
        )

        self.session.add(created_app_user)
        self.session.commit()

        all_user_count = self.session.query(AppUser).count()
        all_users = self.session.query(AppUser).all()

        self.assertEqual(all_user_count, 1)
        for user in all_users:
            returned_django_user = user.get_django_user()
            self.assertIsNone(returned_django_user)
