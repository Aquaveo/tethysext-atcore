import unittest
import uuid
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from tethysext.atcore.models.app_users import AppUsersBase, AppUser

from tethysext.atcore.tests import APP_USER_TEST_DB


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(APP_USER_TEST_DB)
    connection = engine.connect()
    transaction = connection.begin()
    AppUsersBase.metadata.create_all(connection)

    # If you want to insert fixtures to the DB, do it here


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class AppUserTests(unittest.TestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.username = "test_user"
        self.role = "tester"
        self.is_active = True

        self.user = AppUser(
            username=self.username,
            role=self.role,
            is_active=self.is_active,
        )

        self.session.add(self.user)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_create_user(self):
        all_user_count = self.session.query(AppUser).count()
        all_users = self.session.query(AppUser).all()

        self.assertEqual(all_user_count, 1)
        for user in all_users:
            self.assertEqual(user.username, self.username)
            self.assertEqual(user.role, self.role)
            self.assertEqual(user.is_active, self.is_active)
            self.assertIsNotNone(user.id)
            self.assertIsInstance(user.id, uuid.UUID)
