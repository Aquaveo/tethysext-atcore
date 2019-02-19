"""
********************************************************************************
* Name: map_view.py
* Author: nswain
* Created On: November 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock

# Patch the permission_required decorator
# mock.patch('tethys_apps.decorators.permission_required').start()
from tethysext.atcore.tests.factories.django_user import UserFactory

from django.test import RequestFactory
from django.http import HttpResponse
from sqlalchemy.orm.session import Session
from tethys_sdk.testing import TethysTestCase
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource, AppUsersBase
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager

from sqlalchemy.engine import create_engine
from tethysext.atcore.tests import TEST_DB_URL
from tethysext.atcore.services.app_users.roles import Roles

import json


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    AppUsersBase.metadata.create_all(connection)


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class MapViewTests(TethysTestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)
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

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.map_view.render')
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
        self.assertIn('map_title', context)
        self.assertIn('map_subtitle', context)
        self.assertIn('can_use_geocode', context)
        self.assertIn('can_use_plot', context)
        self.assertIn('back_url', context)
        self.assertIn('plot_slide_sheet', context)
        self.assertEqual(mock_render(), response)

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.map_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_no_resource_id(self, mock_has_permission, mock_render, _):
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user

        response = self.controller(request=mock_request, resource_id=None, back_url='/foo/bar')

        mock_has_permission.assert_any_call(mock_request, 'use_map_geocode')
        mock_has_permission.assert_any_call(mock_request, 'use_map_plot')

        render_call_args = mock_render.call_args_list
        context = render_call_args[0][0][2]
        self.assertIn('map_view', context)
        self.assertIn('map_extent', context)
        self.assertIn('layer_groups', context)
        self.assertIn('is_in_debug', context)
        self.assertIn('map_title', context)
        self.assertIn('map_subtitle', context)
        self.assertIn('can_use_geocode', context)
        self.assertIn('can_use_plot', context)
        self.assertIn('back_url', context)
        self.assertIn('plot_slide_sheet', context)
        self.assertEqual(mock_render(), response)

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.map_view.isinstance')
    def test_get_no_resource_permissions(self, mock_isinstance, mock_resource):
        mock_resource.return_value = 'foo'
        mock_isinstance.return_value = True
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user
        response = self.controller(request=mock_request, resource_id=resource_id, back_url='/foo/bar')
        self.assertEqual('foo', response)

    @mock.patch('tethysext.atcore.controllers.map_view.redirect')
    @mock.patch('tethysext.atcore.controllers.map_view.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.get_resource')
    def test_get_no_resource_data_base_id_error(self, mock_resource, mock_messages, mock_redirect):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user
        mock_res_ret = mock.MagicMock()
        mock_resource.return_value = mock_res_ret
        mock_res_ret.get_attribute.return_value = ""
        self.controller(request=mock_request, resource_id=resource_id, back_url='/foo/bar')
        meg_call_args = mock_messages.error.call_args_list
        self.assertIn('/foo/bar/map-view/', str(meg_call_args[0][0][0]))
        self.assertEqual('An unexpected error occurred. Please try again.', meg_call_args[0][0][1])
        mock_redirect.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.default_back_url')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.find_location_by_query')
    def test_post_location_by_query(self, mock_flaq, _):
        resource_id = '12345'
        mock_request = self.request_factory.post('/foo/bar/map-view/',
                                                 data={'method': 'find-location-by-query'})
        mock_request.user = self.django_user
        self.controller(mock_request, resource_id=resource_id)
        mock_flaq.called_assert_with(mock_request, resource_id=resource_id)

    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.default_back_url')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.find_location_by_advanced_query')
    def test_post_location_by_advanced_query(self, mock_flaq, _):
        resource_id = '12345'
        mock_request = self.request_factory.post('/foo/bar/map-view/',
                                                 data={'method': 'find-location-by-advanced-query'})
        mock_request.user = self.django_user
        self.controller(mock_request, resource_id=resource_id)
        mock_flaq.called_assert_with(mock_request, resource_id=resource_id)

    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.default_back_url')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_plot_data')
    def test_post_get_plot(self, mock_plot, _):
        resource_id = '12345'
        mock_request = self.request_factory.post('/foo/bar/map-view/', data={'method': 'get-plot-data'})
        mock_request.user = self.django_user
        self.controller(mock_request, resource_id=resource_id)
        mock_plot.called_assert_with(mock_request, resource_id=resource_id)

    @mock.patch('django.http.response.HttpResponseNotFound')
    def test_post_httpresponsenotfound(self, _):
        mock_request = mock.MagicMock(POST={})
        resource_id = '12345'

        mv = MapView()
        mv.post(request=mock_request, resource_id=resource_id)
        pass

    def test_should_disable_basemap(self):
        mv = MapView()
        self.assertFalse(mv.should_disable_basemap(request='Test1', model_db='model_db', map_manager='map_mange'))

    def test_get_context(self):
        mv = MapView()
        self.assertEqual('context', mv.get_context(request='r', context='context', resource_id='12345', model_db='m',
                                                   map_manager='m'))

    def test_get_permissions(self):
        mv = MapView()
        self.assertEqual('permissions', mv.get_permissions(request='r', permissions='permissions', model_db='m',
                                                           map_manager='m'))

    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.get_resource')
    def test_get_plot_data(self, mock_resource):
        mock_request = mock.MagicMock()

        self.mock_mm().get_plot_for_layer_feature.return_value = ('foo', 'bar', 'bazz')

        # call the method
        ret = self.mv.get_plot_data(mock_request, '12345', 'layer name', 'feature id')

        # test the results
        self.assertEqual(200, ret.status_code)
        mock_resource.assert_called_with(mock_request, '12345')

    @mock.patch('tethysext.atcore.controllers.map_view.redirect')
    @mock.patch('tethysext.atcore.controllers.map_view.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.get_resource')
    def test_get_plot_data_no_db_id(self, mock_resource, mock_messages, mock_redirect):
        mock_request = mock.MagicMock()
        mock_res_ret = mock.MagicMock()
        mock_resource.return_value = mock_res_ret
        mock_res_ret.get_attribute.return_value = ""
        self.mv.back_url = '/foo/bar/'

        self.mock_mm().get_plot_for_layer_feature.return_value = ('foo', 'bar', 'bazz')

        # call the method
        self.mv.get_plot_data(mock_request, '12345', 'layer name', 'feature id')

        # test the results
        meg_call_args = mock_messages.error.call_args_list
        self.assertEqual('An unexpected error occurred. Please try again.', meg_call_args[0][0][1])
        mock_redirect.assert_called()

    @mock.patch('tethysext.atcore.controllers.map_view.isinstance')
    @mock.patch('tethysext.atcore.controllers.app_users.base.AppUsersResourceController.get_resource')
    def test_post_get_plot_data_permissions(self, mock_get_resource, _):
        mock_get_resource.return_value = 'Success'

        # call the method
        ret = self.mv.get_plot_data(mock.MagicMock(), '', '', '')

        # test the results
        self.assertEqual('Success', ret)

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

    def test_find_location_by_advanced_query_no_address_in_bounds(self):
        # TODO No bound case needed
        pass
