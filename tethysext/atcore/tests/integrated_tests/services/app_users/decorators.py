"""
********************************************************************************
* Name: decorators.py
* Author: nswain
* Created On: May 16, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect
from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session, sessionmaker
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethys_apps.base.controller import TethysController
from tethysext.atcore.models.app_users import initialize_app_users_db, AppUser
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests import TEST_DB_URL
from django.test.utils import override_settings


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()

    # Initialize db with staff user
    initialize_app_users_db(connection)


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class MockController(TethysController):
    sessionmaker = None

    def get_app_user_model(self):
        return AppUser

    def get_sessionmaker(self):
        return self.sessionmaker

    @active_user_required()
    def get(self, request, *args, **kwargs):
        return 'SUCCESS'


class ActiveUserRequiredDecoratorTests(TethysTestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/foo/bar/')

        # Setup mock controller
        self.mock_controller = MockController.as_controller(
            sessionmaker=sessionmaker(bind=connection)
        )

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def assertIsRedirect(self, response, to='/apps/'):
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(302, response.status_code)
        self.assertEqual(to, response.url)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def test_no_request_user(self):
        self.request.user = None
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response, to='/accounts/login/?next=/foo/bar/')

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def test_anonymous_user(self):
        self.request.user = AnonymousUser()
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response, to='/accounts/login/?next=/foo/bar/')

    def test_staff_user(self):
        staff_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'
        )
        self.request.user = staff_user
        response = self.mock_controller(self.request)
        self.assertEqual('SUCCESS', response)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    @mock.patch('django.contrib.messages.warning')
    def test_app_user_is_none(self, _):
        user = UserFactory()
        self.request.user = user
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    @mock.patch('django.contrib.messages.warning')
    def test_app_user_not_active(self, _):
        user = UserFactory()
        app_user = AppUser(
            username=user.username,
            role=AppUser.ROLES.ORG_USER,
            is_active=False
        )
        self.session.add(app_user)
        self.session.commit()
        self.request.user = user
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response)

    @mock.patch('django.contrib.messages.warning')
    def test_valid_app_user(self, _):
        user = UserFactory()
        app_user = AppUser(
            username=user.username,
            role=AppUser.ROLES.ORG_USER
        )
        self.session.add(app_user)
        self.session.commit()
        self.request.user = user
        response = self.mock_controller(self.request)
        self.assertEqual('SUCCESS', response)
