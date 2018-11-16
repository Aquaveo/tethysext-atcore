"""
********************************************************************************
* Name: map_view.py
* Author: nswain
* Created On: November 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.spatial_manager import SpatialManager
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


class MapViewTests(TethysTestCase):

    def setUp(self):
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
            _SpatialManager=mock.MagicMock(spec=SpatialManager),
        )
        self.resource_id = 'abc123'
        self.user = UserFactory()
        self.request_factory = RequestFactory()

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.controllers.map_view.MapView._get_back_controller')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView._get_resource')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_back_url', return_value='/foo/')
    @mock.patch('tethysext.atcore.controllers.map_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get(self, mock_has_permission, mock_render, _, __, ___):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.user

        response = self.controller(request=mock_request, resource_id=resource_id)

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

    def test_get_no_resource_permissions(self):
        pass
        # TODO: GAGE FINISH TESTS

    def test_no_database_id(self):
        pass

    def test_post_location_query(self):
        pass

    def test_post_advanced_location_query(self):
        pass

    def test_post_get_plot_data(self):
        pass

    def test_should_disable_basemap(self):
        pass

    def test_get_context(self):
        pass

    def test_get_permissions(self):
        pass

    def test_get_back_url(self):
        pass

    def test__get_back_controller(self):
        pass

    def test_get_plot_data(self):
        pass

    def test_find_location_by_query(self):
        pass

    def test_find_location_by_query_non_200_response(self):
        pass

    def test_find_location_by_query_no_bounds_in_address(self):
        pass

    def test_find_location_by_advanced_query(self):
        pass

    def test_find_location_by_advanced_query_non_200_response(self):
        pass

    def test_find_location_by_advanced_query_no_bounds_in_address(self):
        pass
