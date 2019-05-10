"""
********************************************************************************
* Name: map_view.py
* Author: nswain
* Created On: November 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
import mock
from tethysext.atcore.tests.factories.django_user import UserFactory
from django.test import RequestFactory
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MapViewTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.mock_map_manager = mock.MagicMock(spec=MapManagerBase)
        self.mock_map_manager().compose_map.return_value = (
            mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        )
        self.controller = MapView.as_controller(
            _app=mock.MagicMock(spec=TethysAppBase),
            _AppUser=mock.MagicMock(spec=AppUser),
            _Organization=mock.MagicMock(spec=Organization),
            _Resource=mock.MagicMock(spec=Resource),
            _PermissionsManager=mock.MagicMock(spec=AppPermissionsManager),
            _MapManager=self.mock_map_manager,
            _ModelDatabase=mock.MagicMock(spec=ModelDatabase),
            _SpatialManager=mock.MagicMock(spec=ModelDBSpatialManager),
        )
        self.mock_mm = mock.MagicMock()
        self.mv = MapView(
            _app=mock.MagicMock(spec=TethysAppBase),
            _AppUser=mock.MagicMock(spec=AppUser),
            _Organization=mock.MagicMock(spec=Organization),
            _Resource=mock.MagicMock(spec=Resource),
            _PermissionsManager=mock.MagicMock(spec=AppPermissionsManager),
            _MapManager=self.mock_mm,
            _ModelDatabase=mock.MagicMock(spec=ModelDatabase),
            _SpatialManager=mock.MagicMock(spec=ModelDBSpatialManager),
        )

        self.resource_id = 'abc123'
        self.django_user = UserFactory()
        self.django_user.is_staff = True
        self.django_user.is_superuser = True
        self.django_user.save()

        self.app_user = AppUser(
            username=self.django_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )
        self.session.add(self.app_user)
        self.session.commit()
        self.request_factory = RequestFactory()

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get(self, mock_has_permission, mock_render, _):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user

        response = self.controller(request=mock_request, resource_id=resource_id, back_url='/foo/bar')

        mock_has_permission.assert_any_call(mock_request, 'use_map_geocode')
        mock_has_permission.assert_any_call(mock_request, 'use_map_plot')

        render_call_args = mock_render.call_args_list
        context = render_call_args[0][0][2]
        self.assertIn('resource', context)
        self.assertIn('map_view', context)
        self.assertIn('map_extent', context)
        self.assertIn('layer_groups', context)
        self.assertIn('is_in_debug', context)
        self.assertIn('nav_title', context)
        self.assertIn('nav_subtitle', context)
        self.assertIn('can_use_geocode', context)
        self.assertIn('can_use_plot', context)
        self.assertIn('back_url', context)
        self.assertIn('plot_slide_sheet', context)
        self.assertEqual(mock_render(), response)

    @mock.patch('tethysext.atcore.controllers.resource_view.ResourceView.request_to_method')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_with_method(self, mock_has_permission, mock_render, _, mock_mrtm):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/', data={'method': 'foo'})
        mock_request.user = self.django_user
        mock_method = mock.MagicMock()
        mock_mrtm.return_value = mock_method

        response = self.controller(request=mock_request, resource_id=resource_id, back_url='/foo/bar')

        mock_method.assert_called()
        self.assertEqual(mock_method(), response)

    @mock.patch('tethysext.atcore.services.app_users.decorators.log')
    @mock.patch('tethysext.atcore.services.app_users.decorators.redirect')
    @mock.patch('tethysext.atcore.services.app_users.decorators.messages')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_no_resource_id(self, _, __, ___, mock_messages, mock_redirect, mock_log):
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user

        self.controller(request=mock_request, resource_id=None, back_url='/foo/bar')

        meg_call_args = mock_messages.error.call_args_list
        self.assertIn('/foo/bar/map-view/', str(meg_call_args[0][0][0]))
        self.assertEqual("We're sorry, an unexpected error has occurred.", meg_call_args[0][0][1])
        mock_log.exception.assert_called()
        mock_redirect.assert_called()

    @mock.patch('tethysext.atcore.services.app_users.decorators.log')
    @mock.patch('tethysext.atcore.services.app_users.decorators.redirect')
    @mock.patch('tethysext.atcore.services.app_users.decorators.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.get_resource')
    def test_get_no_resource_database_id_error(self, mock_resource, mock_messages, mock_redirect, mock_log):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user
        mock_res_ret = mock.MagicMock()
        mock_resource.return_value = mock_res_ret
        mock_res_ret.get_attribute.return_value = ""
        self.controller(request=mock_request, resource_id=resource_id, back_url='/foo/bar')
        meg_call_args = mock_messages.error.call_args_list
        self.assertIn('/foo/bar/map-view/', str(meg_call_args[0][0][0]))
        self.assertEqual("We're sorry, an unexpected error has occurred.", meg_call_args[0][0][1])
        mock_log.exception.assert_called()
        mock_redirect.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.default_back_url')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.find_location_by_query')
    def test_post_location_by_query(self, mock_flaq, _):
        resource_id = '12345'
        mock_request = self.request_factory.post('/foo/bar/map-view/',
                                                 data={'method': 'find-location-by-query'})
        mock_request.user = self.django_user
        self.controller(mock_request, resource_id=resource_id)
        mock_flaq.called_assert_with(mock_request, resource_id=resource_id)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.default_back_url')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.find_location_by_advanced_query')
    def test_post_location_by_advanced_query(self, mock_flaq, _):
        resource_id = '12345'
        mock_request = self.request_factory.post('/foo/bar/map-view/',
                                                 data={'method': 'find-location-by-advanced-query'})
        mock_request.user = self.django_user
        self.controller(mock_request, resource_id=resource_id)
        mock_flaq.called_assert_with(mock_request, resource_id=resource_id)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.default_back_url')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_plot_data')
    def test_post_get_plot(self, mock_plot, _):
        resource_id = '12345'
        mock_request = self.request_factory.post('/foo/bar/map-view/', data={'method': 'get-plot-data'})
        mock_request.user = self.django_user
        self.controller(mock_request, resource_id=resource_id)
        mock_plot.called_assert_with(mock_request, resource_id=resource_id)

    @mock.patch('tethysext.atcore.controllers.resource_view.HttpResponseNotFound')
    def test_post_httpresponsenotfound(self, mock_hrnf):
        mock_request = mock.MagicMock(POST={})
        resource_id = '12345'

        mv = MapView()
        mv.get_resource = mock.MagicMock(return_value=mock.MagicMock())
        mv.get_sessionmaker = mock.MagicMock()
        mv.post(request=mock_request, resource_id=resource_id)
        mock_hrnf.assert_called()

    def test_should_disable_basemap(self):
        mv = MapView()
        self.assertFalse(mv.should_disable_basemap(request='Test1', model_db='model_db', map_manager='map_mange'))

    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_permissions(self, mock_hp):
        mv = MapView()
        mock_request = mock.MagicMock()
        permissions = mv.get_permissions(request=mock_request, permissions={}, model_db=mock.MagicMock(),
                                         map_manager=mock.MagicMock())
        self.assertIn('can_use_geocode', permissions)
        self.assertIn('can_use_plot', permissions)
        mock_hp.assert_any_call(mock_request, 'use_map_geocode')
        mock_hp.assert_any_call(mock_request, 'use_map_plot')

    def test_get_plot_data(self):
        mock_request = mock.MagicMock(POST={'layer_name': 'foo', 'feature_id': '123'})

        self.mock_mm().get_plot_for_layer_feature.return_value = ('foo', 'bar', 'bazz')

        # call the method
        self.mv.get_resource = mock.MagicMock()
        ret = self.mv.get_plot_data(
            request=mock_request,
            session=mock.MagicMock(),
            resource=mock.MagicMock()
        )

        # test the results
        self.assertEqual(200, ret.status_code)
        self.mock_mm().get_plot_for_layer_feature.assert_called_with('foo', '123')

    @mock.patch('tethysext.atcore.controllers.map_view.redirect')
    @mock.patch('tethysext.atcore.controllers.map_view.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.get_resource')
    def test_get_plot_data_no_db_id(self, mock_resource, mock_messages, mock_redirect):
        mock_request = mock.MagicMock()
        mock_res_ret = mock.MagicMock()
        mock_resource.return_value = mock_res_ret
        mock_res_ret.get_attribute.return_value = ""
        self.mv.back_url = '/foo/bar/'

        self.mock_mm().get_plot_for_layer_feature.return_value = ('foo', 'bar', 'bazz')

        # call the method
        self.mv.get_plot_data(
            request=mock_request,
            session=mock.MagicMock(),
            resource=None
        )

        # test the results
        meg_call_args = mock_messages.error.call_args_list
        self.assertEqual('An unexpected error occurred. Please try again.', meg_call_args[0][0][1])
        mock_redirect.assert_called()

    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_find_location_by_query(self, _):
        address = '3210 N Canyon Rd, Provo, UT 84604'
        extent = [40.273630, -111.653541, 40.2780, -111.648369]
        request = self.request_factory.post('/foo/bar/map-view/',
                                            data={'method': 'find-location-by-query',
                                                  'q': address,
                                                  'extent': extent},
                                            )

        request.user = self.django_user
        mv = MapView()
        res = mv.find_location_by_query(request, '')

        self.assertEqual(200, res.status_code)

    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch('tethysext.atcore.controllers.map_view.requests')
    def test_find_location_by_query_non_200_response(self, mock_request, _):
        address = '3210 N Canyon Rd, Provo, UT 84604'
        extent = [51.2867, 51.6918741, -0.5103, 0.334]
        request = self.request_factory.post('/foo/bar/map-view/', data={'method': 'find-location-by-query',
                                                                        'q': address, 'extent': extent},)

        request.user = self.django_user

        mock_request.get().status_code = 205
        mock_request.get().text = 'error in request'
        mock_request.get()

        mv = MapView()

        res = mv.find_location_by_query(request, '')

        content = json.loads(res.content.decode('utf-8'))

        self.assertFalse(content['success'])
        self.assertEqual('error in request', content['error'])

    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_find_location_by_query_address_with_no_bounds(self, _):
        address = '3210 N Canyon Rd, Provo, UT 84604'
        request = self.request_factory.post('/foo/bar/map-view/',
                                            data={'method': 'find-location-by-query',
                                                  'q': address,
                                                  'extent': None},
                                            )

        request.user = self.django_user
        mv = MapView()
        res = mv.find_location_by_query(request, '')

        self.assertEqual(200, res.status_code)

    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_find_location_by_advanced_query(self, _):
        address = '3210 N Canyon Rd, Provo, UT 84604'
        request = self.request_factory.post('/foo/bar/map-view/',
                                            data={'method': 'find-location-by-query',
                                                  'q': address})
        request.user = self.django_user

        mv = MapView()

        res = mv.find_location_by_advanced_query(request, '')

        self.assertEqual(200, res.status_code)

    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch('tethysext.atcore.controllers.map_view.requests')
    def test_find_location_by_advanced_query_non_200_response(self, mock_request, _):
        address = '3210 N Canyon Rd, Provo, UT 84604'
        request = self.request_factory.post('/foo/bar/map-view/',
                                            data={'method': 'find-location-by-query',
                                                  'q': address}, )

        request.user = self.django_user

        mock_request.get().status_code = 205
        mock_request.get().text = 'error in request'
        mock_request.get()

        mv = MapView()

        res = mv.find_location_by_advanced_query(request, '')

        content = json.loads(res.content.decode('utf-8'))

        self.assertFalse(content['success'])
        self.assertEqual('error in request', content['error'])
