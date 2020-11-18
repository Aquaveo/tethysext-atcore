"""
********************************************************************************
* Name: map_view_tests.py
* Author: nswain, mlebaron
* Created On: November 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
from unittest import mock
from tethysext.atcore.tests.factories.django_user import UserFactory
from django.test import RequestFactory
from django.http import JsonResponse
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


class NoTitleView(MapView):
    map_title = 'this_title'

    def get_model_db(self, request, resource, *args, **kwargs):
        """
        Need to override this for now, b/c the default implementation does not allow for the resource being None.
        """
        return mock.MagicMock(spec=ModelDatabase)

    def get_managers(self, request, resource, *args, **kwargs):
        """
        Need to override this for now, b/c the default implementation does not allow for the resource being None.
        """
        mock_map_manager = mock.MagicMock(spec=MapManagerBase)
        mock_map_manager.compose_map.return_value = mock.MagicMock(), mock.MagicMock(), mock.MagicMock()

        return mock.MagicMock(spec=ModelDatabase), mock_map_manager


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
        self.assertIn('layer_tab_name', context)
        self.assertEqual('Layers', context['layer_tab_name'])
        self.assertEqual(mock_render(), response)

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_no_title(self, mock_has_permission, mock_render, _):
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user

        controller = NoTitleView.as_controller(
            _app=mock.MagicMock(spec=TethysAppBase),
            _AppUser=mock.MagicMock(spec=AppUser),
            _Organization=mock.MagicMock(spec=Organization),
            _Resource=mock.MagicMock(spec=Resource),
            _PermissionsManager=mock.MagicMock(spec=AppPermissionsManager),
            _MapManager=self.mock_map_manager,
            _ModelDatabase=mock.MagicMock(spec=ModelDatabase),
            _SpatialManager=mock.MagicMock(spec=ModelDBSpatialManager),
        )

        response = controller(request=mock_request, resource_id=None, back_url='/foo/bar')

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
        self.assertEqual(NoTitleView.map_title, context['nav_title'])
        self.assertIn('nav_subtitle', context)
        self.assertIn('can_use_geocode', context)
        self.assertIn('can_use_plot', context)
        self.assertIn('back_url', context)
        self.assertIn('plot_slide_sheet', context)
        self.assertEqual(mock_render(), response)

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_id_is_custom_layer(self, mock_has_permission, mock_render, _):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user
        self.mock_map_manager().compose_map.return_value = (
            mock.MagicMock(), mock.MagicMock(), [{'id': 'custom_layers'}]
        )

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

    @mock.patch('django.conf.settings')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_layer_dropdown_toggle(self, mock_has_permission, mock_render, _, mock_settings):
        resource_id = '12345'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user
        setattr(mock_settings, 'ENABLE_OPEN_PORTAL', True)

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
        self.assertIn('layer_dropdown_toggle', context)
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

    def test_save_custom_layers(self):
        resource = Resource(
            name='Foo',
            description='Bar',
            created_by='user1'
        )
        mock_request = mock.MagicMock(POST={'layer_name': 'foo',
                                            'uuid': '012345',
                                            'service_link': 'my_link',
                                            'service_type': 'type',
                                            'service_layer_name': 'sln',
                                            'feature_id': '123'})
        expected = [b'{"success": true}']

        response = MapView().save_custom_layers(mock_request, self.session, resource)

        self.assertEqual(expected, response.__dict__['_container'])

    def test_remove_custom_layer(self):
        resource = Resource(
            name='Foo',
            description='Bar',
            created_by='user1'
        )
        resource.set_attribute('custom_layers', [{'layer_id': 'layer1'}, {'layer_id': 'layer2'}])
        # resource.set_attribute('custom_layers', ['layer1', 'layer2'])
        mock_request = mock.MagicMock(POST={'layer_id': 'layer2',
                                            'layer_group_type': 'custom_layers'})
        expected = [b'{"success": true}']

        response = MapView().remove_custom_layer(mock_request, self.session, resource)

        self.assertEqual(expected, response.__dict__['_container'])
        self.assertEqual('{"custom_layers": [{"layer_id": "layer1"}]}', resource.__dict__['_attributes'])

    def test_remove_custom_layer_zero_custom_layers(self):
        resource = Resource(
            name='Foo',
            description='Bar',
            created_by='user1'
        )
        resource.set_attribute('custom_layers', [{'layer_id': 'layer1'}])
        mock_request = mock.MagicMock(POST={'layer_id': '2',
                                            'layer_group_type': 'custom_layers'})
        expected = [b'{"success": true}']

        response = MapView().remove_custom_layer(mock_request, self.session, resource)

        self.assertEqual(expected, response.__dict__['_container'])
        self.assertEqual('{"custom_layers": [{"layer_id": "layer1"}]}', resource.__dict__['_attributes'])

    def test_remove_custom_layer_not_custom(self):
        resource = Resource(
            name='Foo',
            description='Bar',
            created_by='user1'
        )
        resource.set_attribute('custom_layers', [{'layer_id': 'layer1'}])
        mock_request = mock.MagicMock(POST={'layer_id': '2',
                                            'layer_group_type': 'layer2'})
        expected = [b'{"success": true}']

        response = MapView().remove_custom_layer(mock_request, self.session, resource)

        self.assertEqual(expected, response.__dict__['_container'])
        self.assertEqual('{"custom_layers": [{"layer_id": "layer1"}]}', resource.__dict__['_attributes'])

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
                                                  'extent': [1, 2, 3, 4]},
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

    def init_expected_response_blgti(self):
        """
        Create variables with chunks of the expected response of the build_layer_group_tree_item method.
        Returns:

        """
        self.layer_group_label = \
            '<li id="123" class="layer-group-item">\n' \
            '  \n' \
            '  <label class="flatmark"><span class="display-name">Fake Layers</span>\n' \
            '    <input type="checkbox"\n' \
            '           class="layer-group-visibility-control"\n' \
            '           checked="checked"\n' \
            '           data-layer-group-id="123">\n' \
            '    <span class="checkmark checkbox"></span>\n' \
            '  </label>'

        self.layer_1_label = \
            '  <label class="flatmark"><span class="display-name">Layer 1</span>\n' \
            '    <input type="checkbox"\n' \
            '           class="layer-visibility-control"\n' \
            '           checked="checked"\n' \
            '           \n' \
            '           data-layer-id="456"\n' \
            '           data-layer-variable="layer-1-var"\n' \
            '           name="123">\n' \
            '    <span class="checkmark checkbox"></span>\n' \
            '  </label>'

        self.layer_2_label = \
            '  <label class="flatmark"><span class="display-name">Layer 2</span>\n' \
            '    <input type="checkbox"\n' \
            '           class="layer-visibility-control"\n' \
            '           checked="checked"\n' \
            '           \n' \
            '           data-layer-id="789"\n' \
            '           data-layer-variable="layer-2-var"\n' \
            '           name="123">\n' \
            '    <span class="checkmark checkbox"></span>\n' \
            '  </label>'

        self.lg_dropdown_menu = \
            '    <div class="dropdown layers-context-menu pull-right">\n' \
            '      <a id="123--context-menu"\n' \
            '         class="btn btn-xs dropdown-toggle layers-btn"\n' \
            '         data-toggle="dropdown" aria-haspopup="true"\n' \
            '         aria-expanded="true">\n' \
            '        <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '      </a>\n' \
            '      <ul class="dropdown-menu dropdown-menu-right" aria-labeledby="123--context-menu">\n' \
            '        \n' \
            '          <li><a class="rename-action" href="javascript:void(0);">' \
                        '<span class="glyphicon glyphicon-pencil"></span>' \
                        '<span class="command-name">Rename</span>' \
                        '</a></li>\n' \
            '        \n' \
            '        \n' \
            '        <li><a class="remove-action" href="javascript:void(0);" data-remove-type="layer" ' \
                        'data-layer-id="">' \
                        '<span class="glyphicon glyphicon-remove"></span>' \
                        '<span class="command-name">Remove</span>' \
                        '</a></li>\n' \
            '        \n' \
            '        \n' \
            '        \n' \
            '      </ul>\n' \
            '    </div>'  # noqa: E127

        self.layer_1_dropdown_menu = \
            '  <div class="dropdown layers-context-menu pull-right">\n' \
            '    <a id="456--context-menu"\n' \
            '       class="btn btn-xs dropdown-toggle layers-btn "\n' \
            '       data-toggle="dropdown"\n' \
            '       aria-haspopup="true"\n' \
            '       aria-expanded="true">\n' \
            '      <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '    </a>\n' \
            '    <ul class="dropdown-menu dropdown-menu-right" ' \
            'aria-labeledby="456--context-menu">\n' \
            '      \n' \
            '        <li><a class="rename-action" href="javascript:void(0);">' \
            '<span class="glyphicon glyphicon-pencil"></span>' \
            '<span class="command-name">Rename</span>' \
            '</a></li>\n' \
            '      \n' \
            '      \n' \
            '      <li><a class="remove-action" href="javascript:void(0);" data-remove-type="layer" ' \
                    'data-layer-id="456">' \
                    '<span class="glyphicon glyphicon-remove"></span>' \
                    '<span class="command-name">Remove</span>' \
                    '</a></li>'  # noqa: E127

        self.layer_2_dropdown_menu = \
            '  <div class="dropdown layers-context-menu pull-right">\n' \
            '    <a id="789--context-menu"\n' \
            '       class="btn btn-xs dropdown-toggle layers-btn "\n' \
            '       data-toggle="dropdown"\n' \
            '       aria-haspopup="true"\n' \
            '       aria-expanded="true">\n' \
            '      <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '    </a>\n' \
            '    <ul class="dropdown-menu dropdown-menu-right" aria-labeledby="789--context-menu">\n' \
            '      \n' \
            '        <li><a class="rename-action" href="javascript:void(0);">' \
                    '<span class="glyphicon glyphicon-pencil"></span>' \
                    '<span class="command-name">Rename</span>' \
                    '</a></li>\n' \
            '      \n' \
            '      \n' \
            '      <li><a class="remove-action" href="javascript:void(0);" ' \
                    'data-remove-type="layer" data-layer-id="789">' \
                    '<span class="glyphicon glyphicon-remove"></span>' \
                    '<span class="command-name">Remove</span>' \
                    '</a></li>'  # noqa: E127

        self.lg_dropdown_menu_no_remove = \
            '    <div class="dropdown layers-context-menu pull-right">\n' \
            '      <a id="123--context-menu"\n' \
            '         class="btn btn-xs dropdown-toggle layers-btn"\n' \
            '         data-toggle="dropdown" aria-haspopup="true"\n' \
            '         aria-expanded="true">\n' \
            '        <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '      </a>\n' \
            '      <ul class="dropdown-menu dropdown-menu-right" aria-labeledby="123--context-menu">\n' \
            '        \n' \
            '          <li><a class="rename-action" href="javascript:void(0);">' \
            '<span class="glyphicon glyphicon-pencil"></span>' \
            '<span class="command-name">Rename</span>' \
            '</a></li>\n' \
            '        \n' \
            '        \n' \
            '        \n' \
            '        \n' \
            '      </ul>\n' \
            '    </div>'

        self.lg_dropdown_menu_no_rename = \
            '    <div class="dropdown layers-context-menu pull-right">\n' \
            '      <a id="123--context-menu"\n' \
            '         class="btn btn-xs dropdown-toggle layers-btn"\n' \
            '         data-toggle="dropdown" aria-haspopup="true"\n' \
            '         aria-expanded="true">\n' \
            '        <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '      </a>\n' \
            '      <ul class="dropdown-menu dropdown-menu-right" aria-labeledby="123--context-menu">\n' \
            '        \n' \
            '        \n' \
            '        <li><a class="remove-action" href="javascript:void(0);" data-remove-type="layer" ' \
            'data-layer-id="">' \
            '<span class="glyphicon glyphicon-remove"></span>' \
            '<span class="command-name">Remove</span>' \
            '</a></li>\n' \
            '        \n' \
            '        \n' \
            '        \n' \
            '      </ul>\n' \
            '    </div>'

        self.layer_1_dropdown_menu_no_rr = \
            '  <div class="dropdown layers-context-menu pull-right">\n' \
            '    <a id="456--context-menu"\n' \
            '       class="btn btn-xs dropdown-toggle layers-btn "\n' \
            '       data-toggle="dropdown"\n' \
            '       aria-haspopup="true"\n' \
            '       aria-expanded="true">\n' \
            '      <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '    </a>\n' \
            '    <ul class="dropdown-menu dropdown-menu-right" aria-labeledby="456--context-menu">\n'

        self.layer_2_dropdown_menu_no_rr = \
            '  <div class="dropdown layers-context-menu pull-right">\n' \
            '    <a id="789--context-menu"\n' \
            '       class="btn btn-xs dropdown-toggle layers-btn "\n' \
            '       data-toggle="dropdown"\n' \
            '       aria-haspopup="true"\n' \
            '       aria-expanded="true">\n' \
            '      <span class="glyphicon glyphicon-option-vertical"></span>\n' \
            '    </a>\n' \
            '    <ul class="dropdown-menu dropdown-menu-right" aria-labeledby="789--context-menu">\n'

    def test_build_legend_item(self):
        data = {
            'div_id': '"legend_div_id"',
            'minimum': '0.1',
            'maximum': '10',
            'prefix': '"val"',
            'color_prefix': '"color"',
            'first_division': '1',
            'color_ramp': '"Blue"',
            'layer_id': '"layer_id"',
        }
        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        expected_result = \
            '{"success": true, "response": "<ul class=\\"legend-list\\" data-collapsed=\\"false\\">\\n  \\n    ' \
            '<div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n        <p>0.1 </p>\\n        ' \
            '<div class=\\"color-box\\" style=\\"background-color: #f7fbff;\\"></div>\\n      </li>\\n    </div>\\n  ' \
            '\\n    <div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n        <p>1.2 </p>\\n' \
            '        <div class=\\"color-box\\" style=\\"background-color: #deebf7;\\"></div>\\n      </li>\\n    ' \
            '</div>\\n  \\n    <div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n        ' \
            '<p>2.3 </p>\\n        <div class=\\"color-box\\" style=\\"background-color: #c6dbef;\\"></div>\\n      ' \
            '</li>\\n    </div>\\n  \\n    <div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n' \
            '        <p>3.4 </p>\\n        <div class=\\"color-box\\" style=\\"background-color: #9ecae1;\\"></div>' \
            '\\n      </li>\\n    </div>\\n  \\n    <div class=\\"legend-item\\">\\n      ' \
            '<li class=\\"legend-list-item\\">\\n        <p>4.5 </p>\\n        <div class=\\"color-box\\" ' \
            'style=\\"background-color: #6baed6;\\"></div>\\n      </li>\\n    </div>\\n  \\n    ' \
            '<div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n        <p>5.6 </p>\\n        ' \
            '<div class=\\"color-box\\" style=\\"background-color: #4292c6;\\"></div>\\n      </li>\\n    </div>\\n  ' \
            '\\n    <div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n        <p>6.7 </p>\\n' \
            '        <div class=\\"color-box\\" style=\\"background-color: #2171b5;\\"></div>\\n      </li>\\n' \
            '    </div>\\n  \\n    <div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n        ' \
            '<p>7.8 </p>\\n        <div class=\\"color-box\\" style=\\"background-color: #08519c;\\"></div>\\n      ' \
            '</li>\\n    </div>\\n  \\n    <div class=\\"legend-item\\">\\n      <li class=\\"legend-list-item\\">\\n' \
            '        <p>8.9 </p>\\n        <div class=\\"color-box\\" style=\\"background-color: #083582;\\"></div>' \
            '\\n      </li>\\n    </div>\\n  \\n    <div class=\\"legend-item\\">\\n      ' \
            '<li class=\\"legend-list-item\\">\\n        <p>10.0 </p>\\n        <div class=\\"color-box\\" ' \
            'style=\\"background-color: #022259;\\"></div>\\n      </li>\\n    </div>\\n  \\n</ul>", "div_id": ' \
            '"legend_div_id", "color_ramp": "Blue", "division_string": "val1:0.10;color1:#f7fbff;val2:1.20;' \
            'color2:#deebf7;val3:2.30;color3:#c6dbef;val4:3.40;color4:#9ecae1;val5:4.50;color5:#6baed6;val6:5.60;' \
            'color6:#4292c6;val7:6.70;color7:#2171b5;val8:7.80;color8:#08519c;val9:8.90;color9:#083582;val10:10.00;' \
            'color10:#022259", "layer_id": "layer_id"}'

        response = mv.build_legend_item(mock_request, self.session, mock_resource)
        self.assertEqual(json.loads(response.content.decode('utf-8')), json.loads(expected_result))

    def test_build_layer_group_tree_item_create(self):
        data = {
            'status': 'create',
            'layer_group_name': 'Fake Layers',
            'layer_group_id': '123',
            'layer_names': '["Layer 1", "Layer 2"]',
            'layer_ids': '["456", "789"]',
            'layer_legends': '["layer-1-var", "layer-2-var"]'
        }

        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        response = mv.build_layer_group_tree_item(mock_request, self.session, mock_resource)

        self.assertIsInstance(response, JsonResponse)
        response_dict = json.loads(response.content)
        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])
        self.assertIn('response', response_dict)

        self.init_expected_response_blgti()

        self.assertIn(self.layer_group_label, response_dict['response'])
        self.assertIn(self.layer_1_label, response_dict['response'])
        self.assertIn(self.layer_2_label, response_dict['response'])
        self.assertIn(self.lg_dropdown_menu, response_dict['response'])
        self.assertIn(self.layer_1_dropdown_menu, response_dict['response'])
        self.assertIn(self.layer_2_dropdown_menu, response_dict['response'])

    def test_build_layer_group_tree_item_create_no_rename(self):
        data = {
            'status': 'create',
            'layer_group_name': 'Fake Layers',
            'layer_group_id': '123',
            'layer_names': '["Layer 1", "Layer 2"]',
            'layer_ids': '["456", "789"]',
            'layer_legends': '["layer-1-var", "layer-2-var"]',
            'show_rename': 'false',
            'show_remove': 'true'
        }

        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        response = mv.build_layer_group_tree_item(mock_request, self.session, mock_resource)

        self.assertIsInstance(response, JsonResponse)
        response_dict = json.loads(response.content)
        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])
        self.assertIn('response', response_dict)

        self.init_expected_response_blgti()

        self.assertIn(self.layer_group_label, response_dict['response'])
        self.assertIn(self.layer_1_label, response_dict['response'])
        self.assertIn(self.layer_2_label, response_dict['response'])
        self.assertIn(self.lg_dropdown_menu_no_rename, response_dict['response'])
        self.assertIn(self.layer_1_dropdown_menu_no_rr, response_dict['response'])
        self.assertIn(self.layer_2_dropdown_menu_no_rr, response_dict['response'])
        self.assertNotIn('rename-action', response_dict['response'])

    def test_build_layer_group_tree_item_create_no_remove(self):
        data = {
            'status': 'create',
            'layer_group_name': 'Fake Layers',
            'layer_group_id': '123',
            'layer_names': '["Layer 1", "Layer 2"]',
            'layer_ids': '["456", "789"]',
            'layer_legends': '["layer-1-var", "layer-2-var"]',
            'show_rename': 'true',
            'show_remove': 'false'
        }

        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        response = mv.build_layer_group_tree_item(mock_request, self.session, mock_resource)

        self.assertIsInstance(response, JsonResponse)
        response_dict = json.loads(response.content)
        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])
        self.assertIn('response', response_dict)

        self.init_expected_response_blgti()

        self.assertIn(self.layer_group_label, response_dict['response'])
        self.assertIn(self.layer_1_label, response_dict['response'])
        self.assertIn(self.layer_2_label, response_dict['response'])
        self.assertIn(self.lg_dropdown_menu_no_remove, response_dict['response'])
        self.assertIn(self.layer_1_dropdown_menu_no_rr, response_dict['response'])
        self.assertIn(self.layer_2_dropdown_menu_no_rr, response_dict['response'])
        self.assertNotIn('remove-action', response_dict['response'])

    def test_build_layer_group_tree_item_create_no_rename_or_remove(self):
        data = {
            'status': 'create',
            'layer_group_name': 'Fake Layers',
            'layer_group_id': '123',
            'layer_names': '["Layer 1", "Layer 2"]',
            'layer_ids': '["456", "789"]',
            'layer_legends': '["layer-1-var", "layer-2-var"]',
            'show_rename': 'false',
            'show_remove': 'false'
        }

        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        response = mv.build_layer_group_tree_item(mock_request, self.session, mock_resource)

        self.assertIsInstance(response, JsonResponse)
        response_dict = json.loads(response.content)
        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])
        self.assertIn('response', response_dict)

        self.init_expected_response_blgti()

        self.assertIn(self.layer_group_label, response_dict['response'])
        self.assertIn(self.layer_1_label, response_dict['response'])
        self.assertIn(self.layer_2_label, response_dict['response'])
        self.assertNotIn(self.lg_dropdown_menu, response_dict['response'])
        self.assertIn(self.layer_1_dropdown_menu_no_rr, response_dict['response'])
        self.assertIn(self.layer_2_dropdown_menu_no_rr, response_dict['response'])
        self.assertNotIn('remove-action', response_dict['response'])
        self.assertNotIn('rename-action', response_dict['response'])

    def test_build_layer_group_tree_item_append(self):
        data = {
            'status': 'append',
            'layer_group_name': 'Fake Layers',
            'layer_group_id': '123',
            'layer_names': '["Layer 1", "Layer 2"]',
            'layer_ids': '["456", "789"]',
            'layer_legends': '["layer-1-var", "layer-2-var"]',
        }

        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        response = mv.build_layer_group_tree_item(mock_request, self.session, mock_resource)

        self.assertIsInstance(response, JsonResponse)
        response_dict = json.loads(response.content)
        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])
        self.assertIn('response', response_dict)

        self.init_expected_response_blgti()

        self.assertNotIn(self.layer_group_label, response_dict['response'])
        self.assertIn(self.layer_1_label, response_dict['response'])
        self.assertNotIn(self.layer_2_label, response_dict['response'])
        self.assertNotIn(self.lg_dropdown_menu, response_dict['response'])
        self.assertIn(self.layer_1_dropdown_menu, response_dict['response'])
        self.assertNotIn(self.layer_2_dropdown_menu, response_dict['response'])

    def test_build_layer_group_tree_item_append_no_rename_or_remove(self):
        data = {
            'status': 'append',
            'layer_group_name': 'Fake Layers',
            'layer_group_id': '123',
            'layer_names': '["Layer 1", "Layer 2"]',
            'layer_ids': '["456", "789"]',
            'layer_legends': '["layer-1-var", "layer-2-var"]',
            'show_rename': 'false',
            'show_remove': 'false'
        }

        mock_request = self.request_factory.post('/foo/bar/map-view', data=data)
        mock_request.user = self.django_user

        mock_resource = mock.MagicMock(spec=Resource)
        mock_model_db = mock.MagicMock(spec=ModelDatabase)
        mock_map_manager = MapManagerBase(spatial_manager=mock.MagicMock(), model_db=mock_model_db)

        mv = MapView()
        mv.get_managers = mock.MagicMock(return_value=(mock_model_db, mock_map_manager))

        response = mv.build_layer_group_tree_item(mock_request, self.session, mock_resource)

        self.assertIsInstance(response, JsonResponse)
        response_dict = json.loads(response.content)
        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])
        self.assertIn('response', response_dict)

        self.init_expected_response_blgti()

        self.assertNotIn(self.layer_group_label, response_dict['response'])
        self.assertIn(self.layer_1_label, response_dict['response'])
        self.assertNotIn(self.layer_2_label, response_dict['response'])
        self.assertNotIn(self.lg_dropdown_menu, response_dict['response'])
        self.assertIn(self.layer_1_dropdown_menu_no_rr, response_dict['response'])
        self.assertNotIn(self.layer_2_dropdown_menu_no_rr, response_dict['response'])
        self.assertNotIn('remove-action', response_dict['response'])
        self.assertNotIn('rename-action', response_dict['response'])
