"""
********************************************************************************
* Name: mixins.py
* Author: nswain and ckrewson
* Created On: September 24, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from sqlalchemy.orm.exc import NoResultFound
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin, AppUsersResourceControllerMixin
from tethysext.atcore.models.app_users import AppUser, Organization, Resource


class FakeAppUsersController(AppUsersControllerMixin):
    pass


class FakeAppUsersResourceController(AppUsersResourceControllerMixin):
    pass


class AppUsersControllerMixinTests(TethysTestCase):

    def setUp(self):
        self.fauc = FakeAppUsersController()

    def tearDown(self):
        pass

    def test_get_app(self):
        mock_app = mock.MagicMock()
        self.fauc._app = mock_app

        ret = self.fauc.get_app()

        self.assertEqual(mock_app, ret)

    def test_get_app_default(self):
        ret = self.fauc.get_app()

        self.assertIsNone(ret)

    def test_get_app_user_model(self):
        ret = self.fauc.get_app_user_model()

        self.assertEqual(AppUser, ret)

    def test_get_organization_model(self):
        ret = self.fauc.get_organization_model()

        self.assertEqual(Organization, ret)

    def test_get_resource_model(self):
        ret = self.fauc.get_resource_model()

        self.assertEqual(Resource, ret)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppPermissionsManager')
    def test_get_permissions_manager(self, mock_apm):
        mock_app = mock.MagicMock()
        self.fauc._app = mock_app
        self.fauc._PermissionsManager = mock_apm

        ret = self.fauc.get_permissions_manager()

        self.assertEqual(mock_apm(), ret)

    def test_get_sessionmaker_with_app(self):
        mock_app = mock.MagicMock()
        self.fauc._app = mock_app

        ret = self.fauc.get_sessionmaker()

        mock_app.get_persistent_store_database.assert_called_with(self.fauc._persistent_store_name,
                                                                  as_sessionmaker=True)
        self.assertEqual(mock_app.get_persistent_store_database(), ret)

    def test_get_sessionmaker_without_app(self):
        self.assertRaises(NotImplementedError, self.fauc.get_sessionmaker)


class AppUsersResourceControllerMixinTests(TethysTestCase):

    def setUp(self):
        self.srid = '2232'
        self.query = 'Colorado'
        self.resource_id = 'abc123'
        self.user = UserFactory()
        self.request_factory = RequestFactory()
        self.farc = FakeAppUsersResourceController()

    def tearDown(self):
        pass

    def test_get_resource_has_permission(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()
        self.farc.get_sessionmaker = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_back_controller = 'myapp:mycontroller'
        mock_session = self.farc.get_sessionmaker()()
        mock_requests_app_user = self.farc.get_app_user_model().get_app_user_from_request()
        mock_requests_app_user.can_view.return_value = True
        mock_resource = mock_session.query().filter().one()

        ret = self.farc._get_resource(request=mock_request,
                                      resource_id=mock_resource_id,
                                      back_controller=mock_back_controller)

        self.assertEqual(mock_resource, ret)
        mock_session.close.assert_called()

    def test_get_resource_has_permission_with_session(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_back_controller = 'myapp:mycontroller'
        mock_session = mock.MagicMock()
        mock_requests_app_user = self.farc.get_app_user_model().get_app_user_from_request()
        mock_requests_app_user.can_view.return_value = True
        mock_resource = mock_session.query().filter().one()

        ret = self.farc._get_resource(request=mock_request,
                                      resource_id=mock_resource_id,
                                      back_controller=mock_back_controller,
                                      session=mock_session)

        self.assertEqual(mock_resource, ret)
        mock_session.close.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.messages')
    def test_get_resource_no_permission(self, mock_messages, _, mock_redirect):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()
        self.farc.get_sessionmaker = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_back_controller = 'myapp:mycontroller'
        mock_session = self.farc.get_sessionmaker()()
        mock_requests_app_user = self.farc.get_app_user_model().get_app_user_from_request()
        mock_requests_app_user.can_view.return_value = False

        ret = self.farc._get_resource(request=mock_request,
                                      resource_id=mock_resource_id,
                                      back_controller=mock_back_controller)

        self.assertEqual(mock_redirect(), ret)
        mock_messages.warning.assert_called()
        mock_session.close.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.messages')
    def test_get_resource_db_exception(self, mock_messages, _, mock_redirect):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()
        self.farc.get_sessionmaker = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_back_controller = 'myapp:mycontroller'
        mock_session = self.farc.get_sessionmaker()()
        mock_session.query.side_effect = NoResultFound

        ret = self.farc._get_resource(request=mock_request,
                                      resource_id=mock_resource_id,
                                      back_controller=mock_back_controller)

        self.assertEqual(mock_redirect(), ret)
        mock_messages.warning.assert_called()
        mock_session.close.assert_called()
