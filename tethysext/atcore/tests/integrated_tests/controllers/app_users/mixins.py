"""
********************************************************************************
* Name: base.py
* Author: nswain and ckrewson
* Created On: September 24, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from sqlalchemy.orm.exc import NoResultFound
from django.test import RequestFactory
from django.test.utils import override_settings
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin, ResourceViewMixin
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.exceptions import ATCoreException


class FakeAppUsersView(AppUsersViewMixin):
    pass


class FakeResourceView(ResourceViewMixin):
    pass


class AppUsersViewMixinTests(TethysTestCase):

    def setUp(self):
        self.fauc = FakeAppUsersView()

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


class ResourceViewMixinTests(TethysTestCase):

    def setUp(self):
        self.srid = '2232'
        self.query = 'Colorado'
        self.resource_id = 'abc123'
        self.user = UserFactory()
        self.request_factory = RequestFactory()
        self.farc = FakeResourceView()

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
    def test_default_back_url(self, mock_reverse, mock_aa):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_aa.return_value = mock.MagicMock(namespace='test1')

        # Execute the method
        self.farc.default_back_url(mock_request, resource_id=mock_resource_id)

        # test results
        mock_aa.assert_called_with(mock_request)
        call_args = mock_reverse.call_args_list
        self.assertEqual('test1:app_users_resource_details', call_args[0][0][0])
        self.assertEqual('abc123', call_args[0][1]['args'][0])

    def test_get_resource_has_permission(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()
        self.farc.get_sessionmaker = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_session = self.farc.get_sessionmaker()()
        mock_requests_app_user = self.farc.get_app_user_model().get_app_user_from_request()
        mock_requests_app_user.can_view.return_value = True
        mock_resource = mock_session.query().filter().one()

        ret = self.farc.get_resource(request=mock_request, resource_id=mock_resource_id)

        self.assertEqual(mock_resource, ret)
        mock_session.close.assert_called()

    def test_get_resource_has_permission_with_session(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_session = mock.MagicMock()
        mock_requests_app_user = self.farc.get_app_user_model().get_app_user_from_request()
        mock_requests_app_user.can_view.return_value = True
        mock_resource = mock_session.query().filter().one()

        ret = self.farc.get_resource(request=mock_request, resource_id=mock_resource_id, session=mock_session)

        self.assertEqual(mock_resource, ret)
        mock_session.close.assert_not_called()

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def test_get_resource_no_permission(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()
        self.farc.get_sessionmaker = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_session = self.farc.get_sessionmaker()()
        mock_requests_app_user = self.farc.get_app_user_model().get_app_user_from_request()
        mock_requests_app_user.can_view.return_value = False

        self.assertRaises(ATCoreException, self.farc.get_resource, request=mock_request, resource_id=mock_resource_id)

        mock_session.close.assert_called()

    @override_settings(ENABLE_OPEN_PORTAL=True)
    def test_get_resource_open_portal(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_session = mock.MagicMock()
        mock_resource = mock_session.query().filter().one()

        ret = self.farc.get_resource(request=mock_request, resource_id=mock_resource_id, session=mock_session)

        self.assertEqual(mock_resource, ret)
        mock_session.close.assert_not_called()

    def test_get_resource_db_exception(self):
        self.farc.get_app_user_model = mock.MagicMock()
        self.farc.get_resource_model = mock.MagicMock()
        self.farc.get_sessionmaker = mock.MagicMock()

        mock_request = self.request_factory.get('/foo/bar/')
        mock_resource_id = self.resource_id
        mock_session = self.farc.get_sessionmaker()()
        mock_session.query.side_effect = NoResultFound

        self.assertRaises(NoResultFound, self.farc.get_resource, request=mock_request, resource_id=mock_resource_id)

        mock_session.close.assert_called()
