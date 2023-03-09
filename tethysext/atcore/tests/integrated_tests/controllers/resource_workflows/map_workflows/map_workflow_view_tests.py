"""
********************************************************************************
* Name: map_workflow_view_tests.py
* Author: Teva, Tanner, mlebaron
* Created On: December 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from django.test import RequestFactory
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.controllers.resource_workflows.mixins import WorkflowViewMixin
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view import MapWorkflowView
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.resource_workflow_steps.spatial_input_rws import SpatialInputRWS
from tethysext.atcore.models.resource_workflow_steps.spatial_rws import SpatialResourceWorkflowStep
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MapWorkflowViewTests(WorkflowViewTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)

        self.step1 = ResourceWorkflowStep(
            name='name1',
            help='help1',
            order=1
        )

        self.workflow.steps.append(self.step1)
        self.step2 = ResourceWorkflowStep(
            name='name2',
            help='help2',
            order=2
        )

        self.workflow.steps.append(self.step2)
        self.step3 = ResourceWorkflowStep(
            name='name3',
            help='help3',
            order=3
        )
        self.workflow.steps.append(self.step3)

        self.mock_app = TethysAppBase()
        self.mock_app.package = 'test'
        self.mock_app.root_url = 'test'

        self.mock_map_manager = mock.MagicMock(spec=MapManagerBase)
        self.mock_map_manager().compose_map.return_value = (
            mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        )
        self.controller = MapWorkflowView.as_controller(
            _app=self.mock_app,
            _AppUser=mock.MagicMock(spec=AppUser),
            _Organization=mock.MagicMock(spec=Organization),
            _Resource=mock.MagicMock(spec=Resource),
            _PermissionsManager=mock.MagicMock(spec=AppPermissionsManager),
            _MapManager=self.mock_map_manager,
            _SpatialManager=mock.MagicMock(spec=ModelDBSpatialManager),
        )
        self.mock_mm = mock.MagicMock()
        self.mv = MapView(
            _app=self.mock_app,
            _AppUser=mock.MagicMock(spec=AppUser),
            _Organization=mock.MagicMock(spec=Organization),
            _Resource=mock.MagicMock(spec=Resource),
            _PermissionsManager=mock.MagicMock(spec=AppPermissionsManager),
            _MapManager=self.mock_mm,
            _SpatialManager=mock.MagicMock(spec=ModelDBSpatialManager),
        )

        self.map_view = mock.MagicMock()
        layer = SpatialInputRWS(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        layer.feature_selection = False
        layer.editable = False
        self.map_view.layers = [layer]

        self.resource_id = 'abc123'
        self.django_super_user = UserFactory()
        self.django_super_user.is_staff = True
        self.django_super_user.is_superuser = True
        self.django_super_user.save()

        self.django_user = UserFactory()
        self.django_user.save()

        self.app_user = AppUser(
            username=self.django_super_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )

        self.session.add(self.resource)
        self.session.add(self.app_user)
        self.session.commit()
        self.request_factory = RequestFactory()

    def tearDown(self):
        super().tearDown()

    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    @mock.patch.object(ResourceWorkflowView, 'workflow_locked_for_request_user', return_value=False)
    @mock.patch.object(ResourceWorkflowView, 'get_step_url_name')
    @mock.patch.object(WorkflowViewMixin, 'get_step')
    @mock.patch.object(WorkflowViewMixin, 'get_workflow')
    @mock.patch.object(ResourceWorkflowView, 'on_get')
    @mock.patch.object(MapView, 'get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_context(self, mock_has_permission, mock_render, _, mock_on_get, mock_get_workflow,
                         mock_get_step, mock_url, __, ___):
        self.mock_app.get_spatial_dataset_service = mock.MagicMock()
        mock_on_get.return_value = None
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = self.step2
        mock_url.return_value = 'my_workspace:generic_workflow_step'
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_super_user

        response = self.controller(request=mock_request, resource_id=self.resource_id, back_url='./back_url',
                                   workflow_id=self.workflow.id, step_id=self.step1.id)

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

        render_calls = mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        self.assertEqual(mock_render(), response)

    def test_set_feature_selection(self):
        MapWorkflowView().set_feature_selection(self.map_view)

        self.assertTrue(self.map_view.layers[0].feature_selection)
        self.assertTrue(self.map_view.layers[0].editable)

    @mock.patch.object(MapView, 'get_map_manager')
    def test_process_step_options(self, mock_get_map_manager):
        mock_get_map_manager.return_value = MapManagerBase(mock.MagicMock(), mock.MagicMock())
        resource = mock.MagicMock()

        MapWorkflowView().add_layers_for_previous_steps(self.request, resource, self.step3, self.map_view, [])

    @mock.patch('tethys_gizmos.gizmo_options.map_view.log')
    def test_build_mv_layer(self, _):
        self.step2.options['plural_name'] = 'My Plural Name'
        self.step2.options['singular_name'] = 'single_name'

        geo_json = {
            'features': [{
                'properties': {
                    'layer_name': 'before'
                }
            }]
        }
        map_manager = MapManagerBase(mock.MagicMock(), mock.MagicMock())

        layer = MapWorkflowView()._build_mv_layer(self.step2, geo_json, map_manager)

        self.assertIn('source', layer)
        self.assertIn('legend_title', layer)
        self.assertIn('options', layer)
        self.assertIn('editable', layer)
        self.assertIn('layer_options', layer)
        self.assertIn('legend_classes', layer)
        self.assertIn('legend_extent', layer)
        self.assertIn('legend_extent_projection', layer)
        self.assertIn('feature_selection', layer)
        self.assertIn('geometry_attribute', layer)
        self.assertIn('data', layer)
        layer_name = '{}_my_plural_name'.format(str(self.step2.id))
        self.assertEqual(layer_name, layer.options['features'][0]['properties']['layer_name'])
        self.assertTrue(layer.editable)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.log')
    @mock.patch('tethys_gizmos.gizmo_options.map_view.log')
    @mock.patch.object(MapView, 'get_map_manager')
    def test_add_layers_for_previous_steps_no_child(self, mock_get_map_manager, _, __):
        mock_get_map_manager.return_value = MapManagerBase(mock.MagicMock(), mock.MagicMock())
        resource = mock.MagicMock()
        workflow = ResourceWorkflow(name='foo')
        layer_groups = [{}]

        step1 = SpatialInputRWS(
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
            name='name1'
        )
        step1.child = None
        workflow.steps.append(step1)

        step2 = ResourceWorkflowStep(
            name='name2',
            help='help2'
        )
        workflow.steps.append(step2)

        map_view, ret_layer_groups = MapWorkflowView().add_layers_for_previous_steps(self.request, resource, step2,
                                                                                     self.map_view, layer_groups)

        self.assertEqual(self.map_view, map_view)
        self.assertEqual(layer_groups, ret_layer_groups)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.log')
    @mock.patch('tethys_gizmos.gizmo_options.map_view.log')
    @mock.patch.object(MapView, 'get_map_manager')
    def test_add_layers_for_previous_steps_wrong_child_type(self, mock_get_map_manager, _, __):
        mock_get_map_manager.return_value = MapManagerBase(mock.MagicMock(), mock.MagicMock())
        resource = mock.MagicMock()
        workflow = ResourceWorkflow(name='foo')
        layer_groups = [{}]

        step1 = SpatialInputRWS(
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
            name='name1',
            order=1
        )
        workflow.steps.append(step1)

        step2 = ResourceWorkflowStep(
            name='name2',
            help='help2',
            order=2
        )
        workflow.steps.append(step2)
        step1.child = step2

        map_view, ret_layer_groups = MapWorkflowView().add_layers_for_previous_steps(self.request, resource, step2,
                                                                                     self.map_view, layer_groups)

        self.assertEqual(self.map_view, map_view)
        self.assertEqual(layer_groups, ret_layer_groups)

    @mock.patch('tethys_gizmos.gizmo_options.map_view.log')
    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_rws.SpatialResourceWorkflowStep.to_geojson')
    @mock.patch.object(MapView, 'get_map_manager')
    def test_add_layers_for_previous_steps_with_child(self, mock_get_map_manager, mock_to_geojson, _):
        mock_get_map_manager.return_value = MapManagerBase(mock.MagicMock(), mock.MagicMock())
        mock_to_geojson.return_value = {
            'features': [{
                'properties': {
                    'layer_name': 'epicness'
                }
            }]
        }
        resource = mock.MagicMock()
        workflow = ResourceWorkflow(name='foo')
        layer_groups = [{}]

        step1 = SpatialInputRWS(
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
            name='name1',
            order=1
        )
        workflow.steps.append(step1)

        step2 = SpatialResourceWorkflowStep(
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
            name='name2',
            order=2
        )
        workflow.steps.append(step2)
        step1.children = [step2]

        map_view, ret_layer_groups = MapWorkflowView().add_layers_for_previous_steps(self.request, resource, step2,
                                                                                     self.map_view, layer_groups)

        self.assertEqual(self.map_view, map_view)
        self.assertEqual(2, len(ret_layer_groups))
        self.assertIn('id', ret_layer_groups[0])
        self.assertIn('display_name', ret_layer_groups[0])
        self.assertIn('control', ret_layer_groups[0])
        self.assertIn('layers', ret_layer_groups[0])
        self.assertIn('visible', ret_layer_groups[0])
        self.assertIn('toggle_status', ret_layer_groups[0])
        self.assertEqual({}, ret_layer_groups[1])
