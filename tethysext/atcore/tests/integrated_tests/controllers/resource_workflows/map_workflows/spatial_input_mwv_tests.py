"""
********************************************************************************
* Name: spatial_input_mwv_tests.py
* Author: mlebaron
* Created On: August 6, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import pathlib as pl
from unittest import mock
from django.http import HttpRequest, HttpResponseRedirect
from django.core.files.uploadedfile import InMemoryUploadedFile
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.controllers.resource_workflows.mixins import WorkflowViewMixin
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users import AppUser
from django.http import JsonResponse
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.resource_workflow_steps.spatial_input_rws import SpatialInputRWS
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv import SpatialInputMWV
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialInputMwvTests(WorkflowViewTestCase):

    def setUp(self):
        super().setUp()

        tests_dir = pl.Path(__file__).parents[4]
        self.shapefile_dir = tests_dir / 'files' / 'shapefile'
        self.BadProjection_zip = self.shapefile_dir / 'BadProjection.zip'
        self.Detpoly_zip = self.shapefile_dir / 'Detpoly.zip'
        self.MissingPrj_zip = self.shapefile_dir / 'MissingPrj.zip'
        self.MissingSHP_zip = self.shapefile_dir / 'MissingSHP.zip'
        self.Det1poly4326_zip = self.shapefile_dir / 'Det1poly4326.zip'
        self.TestDates4326_zip = self.shapefile_dir / 'TestDates4326.zip'

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        self.context = {}

        # Step 1
        self.step1 = ResourceWorkflowStep(
            name='name1',
            help='help1',
            order=1,
            options={
                'allow_drawing': True,
                'shapes': ['points', 'lines', 'polygons', 'extents'],
                'snapping_enabled': False,
                'snapping_layer': {},
                'snapping_options': {},
                'plural_name': 'my_plural_name',
                'singular_name': 'singular_name'
            }
        )
        self.workflow.steps.append(self.step1)

        # Step 2
        self.step2 = ResourceWorkflowStep(
            name='name2',
            help='help2',
            order=2
        )
        self.workflow.steps.append(self.step2)

        # Step 3
        self.step3 = ResourceWorkflowStep(
            name='name3',
            help='help3',
            order=3
        )
        self.workflow.steps.append(self.step3)

        self.django_user = UserFactory()
        self.django_user.is_staff = True
        self.django_user.is_superuser = True
        self.django_user.save()

        self.app_user = AppUser(
            username=self.django_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )

        self.request.user = self.app_user

        self.session.add(self.resource)
        self.session.add(self.app_user)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=True)
    @mock.patch.object(AppUsersViewMixin, 'get_permissions_manager')
    def test_get_step_specific_context_has_active_role(self, _, __, ___, ____):
        self.step1.active_roles = []
        self.step1.options['allow_shapefile'] = False
        self.step1.options['allow_image'] = False

        ret = SpatialInputMWV().get_step_specific_context(self.request, self.session, self.context, self.step1,
                                                          None, self.step2)

        expected = {
            'allow_shapefile': False,
            'allow_edit_attributes': True,
            'allow_image': False,
        }
        self.assertEqual(expected, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=False)
    @mock.patch.object(AppUsersViewMixin, 'get_permissions_manager')
    def test_get_step_specific_context_no_active_role(self, _, __, ___, ____):
        self.step1.options['allow_shapefile'] = True
        self.step1.options['allow_image'] = True

        ret = SpatialInputMWV().get_step_specific_context(self.request, self.session, self.context, self.step1,
                                                          None, self.step2)

        expected = {
            'allow_shapefile': False,
            'allow_edit_attributes': False,
            'allow_image': False,
        }
        self.assertEqual(expected, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch.object(MapView, 'get_map_manager')
    @mock.patch.object(ResourceWorkflowStep, 'get_parameter')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=False)
    def test_process_step_options_no_attributes_nor_active_role(self, _, mock_params, mock_get_map_manager, __, ___):
        mock_params.return_value = {'geometry': 'shapes and such'}
        map_view = MapView()
        map_view.layers = []
        mock_get_map_manager.return_value = map_view

        resource = mock.MagicMock()
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]

        instance = SpatialInputMWV()
        instance.map_type = 'tethys_map_view'
        instance.process_step_options(self.request, self.session, self.context, resource, self.step1, None, self.step2)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.generate_django_form')
    @mock.patch.object(MapView, 'get_map_manager')
    @mock.patch.object(ResourceWorkflowStep, 'get_parameter')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=True)
    def test_process_step_options_with_attributes_and_active_role(self, _, mock_params, mock_get_map_manager,
                                                                  mock_form, __, ___):
        mock_params.return_value = {'geometry': 'shapes and such'}
        map_view = MapView()
        map_view.layers = []
        mock_get_map_manager.return_value = map_view
        mock_form.return_view = {}

        resource = mock.MagicMock()
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]
        self.step1.options['attributes'] = True

        instance = SpatialInputMWV()
        instance.map_type = 'tethys_map_view'
        instance.process_step_options(self.request, self.session, self.context, resource, self.step1, None, self.step2)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.generate_django_form')
    @mock.patch.object(MapView, 'get_map_manager')
    @mock.patch.object(ResourceWorkflowStep, 'get_parameter')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=True)
    def test_process_step_options_with_param_class(self, _, mock_params, mock_get_map_manager, mock_form, __, ___):
        mock_params.return_value = {'geometry': 'shapes and such'}
        map_view = MapView()
        map_view.layers = []
        mock_get_map_manager.return_value = map_view
        mock_form.return_view = {}

        resource = mock.MagicMock()
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]
        self.step1.options['param_class'] = 'os.test_foo_param_class_doesnt_exist'

        instance = SpatialInputMWV()
        instance.map_type = 'tethys_map_view'
        instance.process_step_options(self.request, self.session, self.context, resource, self.step1, None, self.step2)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch.object(MapView, 'get_map_manager')
    @mock.patch.object(ResourceWorkflowStep, 'get_parameter')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=True)
    def test_process_step_options_unknown_shape(self, _, mock_params, mock_get_map_manager, __, ___):
        mock_params.return_value = {'geometry': 'shapes and such'}
        mock_get_map_manager.return_value = MapView()

        resource = mock.MagicMock()
        map_view = MapView()
        map_view.layers = []
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]
        self.step1.options['shapes'].append('unknown_shape')
        response = None

        try:
            response = SpatialInputMWV().process_step_options(self.request, self.session, self.context, resource,
                                                              self.step1, None, self.step2)
        except RuntimeError as e:
            self.assertEqual('Invalid shapes defined: unknown_shape.', str(e))
        self.assertTrue(response is None)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.is_locked_for_request_user',
                return_value=False)
    @mock.patch('tethysext.atcore.models.app_users.resource.Resource.is_locked_for_request_user',
                return_value=False)
    @mock.patch.object(MapView, 'get_map_manager')
    @mock.patch.object(ResourceWorkflowStep, 'get_parameter')
    @mock.patch.object(ResourceWorkflowView, 'user_has_active_role', return_value=True)
    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_process_step_options_imagery(self, mock_get_app, _, mock_params, mock_get_map_manager, __, ___):
        mock_params.return_value = {'geometry': 'shapes and such'}
        # mock_get_map_manager.return_value = MapView()

        resource = mock.MagicMock()
        map_view = MapView()
        map_view.layers = []
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]
        image = {
            'layer_name': 'test_layer_name',
            'layer_title': 'test_layer_title',
            'layer_variable': 'test_layer_variable',
        }
        self.step1.attributes = {'imagery': [image]}
        response = None

        instance = SpatialInputMWV()
        instance.map_type = 'tethys_map_view'

        try:
            response = instance.process_step_options(self.request, self.session, self.context, resource,
                                                     self.step1, None, self.step2)
        except RuntimeError as e:
            self.assertEqual('Invalid shapes defined: unknown_shape.', str(e))
        self.assertTrue(response is None)
        mock_get_map_manager.return_value.build_wms_layer.assert_called_once()
        mock_get_map_manager.return_value.build_layer_group.assert_called_once()

    @mock.patch.object(ResourceWorkflowStep, 'set_parameter')
    @mock.patch.object(SpatialInputMWV, 'parse_drawn_geometry')
    @mock.patch.object(SpatialInputMWV, 'parse_shapefile')
    def test_process_step_data(self, mock_parse_shp, mock_parse_geom, _):
        mock_parse_shp.return_value = {'features': [{'geometry': {'coordinates': [0, 5], 'type': 'some_type'},
                                                     'properties': {}}]}
        mock_parse_geom.return_value = {'features': [{'geometry': {'coordinates': [1, 6], 'type': 'other_type'},
                                                      'properties': {'id': 7}}]}
        mock_resource = mock.MagicMock()
        self.request.POST = {'geometry': {'value': 'shapes'}}
        self.request.FILES = {'shapefile': 'Det1poly.shp'}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_resource,
                                                       './current', './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./current', response.url)

    @mock.patch.object(ResourceWorkflowStep, 'set_parameter')
    @mock.patch.object(SpatialInputMWV, 'parse_drawn_geometry')
    @mock.patch.object(SpatialInputMWV, 'parse_shapefile')
    def test_process_step_data_no_shapefile(self, mock_parse_shp, mock_parse_geom, _):
        mock_parse_shp.return_value = {'features': [{'geometry': {'coordinates': [0, 5], 'type': 'some_type'},
                                                     'properties': {}}]}
        mock_parse_geom.return_value = {'features': [{'geometry': {'coordinates': [1, 6], 'type': 'other_type'},
                                                      'properties': {'id': 7}}]}
        mock_resource = mock.MagicMock()
        self.request.POST = {'geometry': {'value': 'shapes'}}
        self.request.FILES = {'shapefile': None}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_resource,
                                                       './current', './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./prev', response.url)

    def test_process_step_data_previous(self):
        mock_resource = mock.MagicMock()
        self.request.POST = {'geometry': None, 'previous-submit': True}
        self.request.FILES = {'shapefile': None}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_resource,
                                                       './current', './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./prev', response.url)

    def test_process_step_data_not_previous(self):
        mock_resource = mock.MagicMock()
        self.request.POST = {'geometry': None, 'next-submit': True}
        self.request.FILES = {'shapefile': None}
        self.step1._parameters = {'geometry': {'value': 'shapes'}}
        response = None

        try:
            response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_resource,
                                                           './current', './prev', './next')
        except ValueError as e:
            self.assertEqual('You must either draw at least one singular_name or upload a shapefile of my_plural_name.',
                             str(e))
            self.assertEqual({'geometry': {'value': None}}, self.step1._parameters)
            self.assertTrue(self.step1.dirty)
        self.assertTrue(response is None)

    @mock.patch.object(ResourceWorkflowStep, 'set_parameter')
    @mock.patch.object(SpatialInputMWV, 'store_imagery')
    def test_process_step_data_imagery(self, mock_store_imagery, _):
        test_image = 'foo.tif'
        mock_resource = mock.MagicMock()
        self.request.POST = {'geometry': None}
        self.request.FILES = {'image': test_image}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_resource,
                                                       './current', './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./current', response.url)
        mock_store_imagery.assert_called_once_with(self.request, self.step1, test_image)

    @mock.patch.object(WorkflowViewMixin, 'get_step')
    @mock.patch.object(SpatialInputRWS, 'validate_feature_attributes')
    def test_validate_feature_attributes_success(self, _, mock_get_step):
        step = SpatialInputRWS(
            'geo_server',
            mock.MagicMock(spec=MapManagerBase),
            mock.MagicMock()
        )
        workflow = ResourceWorkflow()
        workflow.steps.append(step)
        mock_get_step.return_value = step
        self.request.POST = mock.MagicMock()

        response = SpatialInputMWV().validate_feature_attributes(self.request, self.session, None, self.step1.id)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual([b'{"success": true}'], response.__dict__['_container'])

    @mock.patch.object(WorkflowViewMixin, 'get_step')
    @mock.patch.object(SpatialInputRWS, 'validate_feature_attributes')
    def test_validate_feature_attributes_error(self, mock_valid_attrib, mock_get_step):
        mock_valid_attrib.side_effect = ValueError('Error message')
        step = SpatialInputRWS(
            'geo_server',
            mock.MagicMock(spec=MapManagerBase),
            mock.MagicMock()
        )
        workflow = ResourceWorkflow()
        workflow.steps.append(step)
        mock_get_step.return_value = step
        self.request.POST = mock.MagicMock()

        response = SpatialInputMWV().validate_feature_attributes(self.request, self.session, None, self.step1.id)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual([b'{"success": false, "error": "Error message"}'], response.__dict__['_container'])

    def test_parse_shapefile_no_file(self):
        shapefile = None

        ret = SpatialInputMWV().parse_shapefile(self.request, shapefile)

        self.assertEqual(None, ret)

    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_parse_shapefile_bad_projection(self, mock_get_app):
        mock_app = TethysAppBase()
        mock_app_path = mock.MagicMock()
        mock_app_path.path = self.shapefile_dir
        mock_app.get_user_workspace = mock.MagicMock(return_value=mock_app_path)
        mock_get_app.return_value = mock_app

        try:
            with open(self.BadProjection_zip, 'rb') as f:
                shapefile = InMemoryUploadedFile(
                    file=f,
                    field_name='shapefile',
                    name='BadProjection.zip',
                    content_type='application/zip',
                    size=955,
                    charset=None
                )

                SpatialInputMWV().parse_shapefile(self.request, shapefile)

                self.assertTrue(False)  # This line should not be reached
        except ValueError as e:
            self.assertEqual('Invalid shapefile provided: Projected coordinate systems are not supported at this time.'
                             ' Please re-project the shapefile to the WGS 1984 Geographic Projection (EPSG:4326).',
                             str(e))

    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_parse_shapefile_missing_shp(self, mock_get_app):
        mock_app = TethysAppBase()
        mock_app_path = mock.MagicMock()
        mock_app_path.path = self.shapefile_dir
        mock_app.get_user_workspace = mock.MagicMock(return_value=mock_app_path)
        mock_get_app.return_value = mock_app

        try:
            with open(self.MissingSHP_zip, 'rb') as f:
                shapefile = InMemoryUploadedFile(
                    file=f,
                    field_name='shapefile',
                    name='MissingSHP.zip',
                    content_type='application/zip',
                    size=955,
                    charset=None
                )

                SpatialInputMWV().parse_shapefile(self.request, shapefile)

                self.assertTrue(False)  # This line should not be hit
        except ValueError as e:
            self.assertEqual('Invalid shapefile provided: No shapefile found in given files.', str(e))

    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_parse_shapefile_missing_prj(self, mock_get_app):
        mock_app = TethysAppBase()
        mock_app_path = mock.MagicMock()
        mock_app_path.path = self.shapefile_dir
        mock_app.get_user_workspace = mock.MagicMock(return_value=mock_app_path)
        mock_get_app.return_value = mock_app

        try:
            with open(self.MissingPrj_zip, 'rb') as f:
                shapefile = InMemoryUploadedFile(
                    file=f,
                    field_name='shapefile',
                    name='MissingPrj.zip',
                    content_type='application/zip',
                    size=1040,
                    charset=None
                )

                SpatialInputMWV().parse_shapefile(self.request, shapefile)

                self.assertTrue(False)  # This line should not be hit
        except ValueError as e:
            self.assertEqual('Invalid shapefile provided: Unable to determine projection of the given shapefile. '
                             'Please include a .prj file.', str(e))

    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_parse_shapefile_valid(self, mock_get_app):
        mock_app = TethysAppBase()
        mock_app_path = mock.MagicMock()
        mock_app_path.path = self.shapefile_dir
        mock_app.get_user_workspace = mock.MagicMock(return_value=mock_app_path)
        mock_get_app.return_value = mock_app

        with open(self.Det1poly4326_zip, 'rb') as f:
            shapefile = InMemoryUploadedFile(
                file=f,
                field_name='shapefile',
                name='Det1poly4326.zip',
                content_type='application/zip',
                size=1040,
                charset=None
            )

            geojson = SpatialInputMWV().parse_shapefile(self.request, shapefile)

        self.assertIn('features', geojson)
        self.assertIn('type', geojson)
        self.assertEqual('FeatureCollection', geojson['type'])
        self.assertEqual(1, len(geojson['features']))
        self.assertIn('coordinates', geojson['features'][0]['geometry'])
        self.assertEqual('Polygon', geojson['features'][0]['geometry']['type'])
        self.assertIn('properties', geojson['features'][0])
        self.assertIn('type', geojson['features'][0])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.geojson')
    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_parse_shapefile_invalid_geojson(self, mock_get_app, mock_geojson):
        mock_app = TethysAppBase()
        mock_app_path = mock.MagicMock()
        mock_app_path.path = self.shapefile_dir
        mock_app.get_user_workspace = mock.MagicMock(return_value=mock_app_path)
        mock_get_app.return_value = mock_app
        geojson_value = mock.MagicMock()
        geojson_value.is_valid = False
        mock_geojson.loads.return_value = geojson_value

        try:
            with open(self.Det1poly4326_zip, 'rb') as f:
                shapefile = InMemoryUploadedFile(
                    file=f,
                    field_name='shapefile',
                    name='Det1poly4326.zip',
                    content_type='application/zip',
                    size=1040,
                    charset=None
                )

                SpatialInputMWV().parse_shapefile(self.request, shapefile)

                self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertIn('An error has occurred while parsing the shapefile: '
                          'Invalid geojson from "shapefile" parameter:', str(e))

    def test_parse_shapefile_generic_exception(self):
        shapefile = InMemoryUploadedFile(
            file='/home/mlebaron/src/tethysext-atcore/tethysext/atcore/tests/files/shapefile/BadProjection.zip',
            field_name='',
            name='BadProjection.zip',
            content_type='',
            size=0,
            charset=''
        )

        try:
            SpatialInputMWV().parse_shapefile(self.request, shapefile)
            self.assertTrue(False)  # This should not be reached
        except RuntimeError as e:
            self.assertIn('An error has occurred while parsing the shapefile:', str(e))

    def test_validate_projection_projcs(self):
        proj_str = 'data PROJCS data'

        try:
            SpatialInputMWV().validate_projection(proj_str)
            self.assertTrue(False)  # This should not be reached
        except ValueError as e:
            self.assertEqual('Projected coordinate systems are not supported at this time. Please re-project '
                             'the shapefile to the WGS 1984 Geographic Projection (EPSG:4326).', str(e))

    def test_validate_projection_geogcs(self):
        proj_str = 'data GEOGCS data'

        try:
            SpatialInputMWV().validate_projection(proj_str)
            self.assertTrue(False)  # This should not be reached
        except ValueError as e:
            self.assertEqual('Only geographic projections are supported at this time. Please re-project shapefile to '
                             'the WGS 1984 Geographic Projection (EPSG:4326).', str(e))

    def test_parse_drawn_geometry_no_geometry(self):
        ret = SpatialInputMWV().parse_drawn_geometry(None)

        self.assertEqual(ret, None)

    def test_parse_drawn_geometry_valid(self):
        geometry_json = '{"type":"GeometryCollection","geometries":[{"type":"Polygon","coordinates":' \
                        '[[[-87.8815269470215,30.646699678521756],[-87.86882400512695,30.644779755892927],' \
                        '[-87.87517547607422,30.641235183209247],[-87.8815269470215,30.646699678521756]]],' \
                        '"properties":{"id":"drawing_layer.2628c0cb-52f5-45ef-8cbe-b19f81c2a10d"},' \
                        '"crs":{"type":"link","properties":' \
                        '{"href":"http://spatialreference.org/ref/epsg/4326/proj4/","type":"proj4"}}}]}'
        expected = {"features": [{"geometry": {"coordinates": [[[-87.881527, 30.6467], [-87.868824, 30.64478], [-87.875175, 30.641235], [-87.881527, 30.6467]]], "crs": {"properties": {"href": "http://spatialreference.org/ref/epsg/4326/proj4/", "type": "proj4"}, "type": "link"}, "type": "Polygon"}, "properties": {"id": "drawing_layer.2628c0cb-52f5-45ef-8cbe-b19f81c2a10d"}, "type": "Feature"}], "type": "FeatureCollection"}  # noqa: E501

        ret = SpatialInputMWV().parse_drawn_geometry(geometry_json)

        self.assertEqual(expected, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.geojson')
    def test_parse_drawn_geometry_invalid(self, mock_geojson):
        geometry_json = '{"type":"GeometryCollection","geometries":[{"type":"Polygon","coordinates":' \
                        '[[[-87.8815269470215,30.646699678521756],[-87.86882400512695,30.644779755892927],' \
                        '[-87.87517547607422,30.641235183209247],[-87.8815269470215,30.646699678521756]]],' \
                        '"properties":{"id":"drawing_layer.2628c0cb-52f5-45ef-8cbe-b19f81c2a10d"},' \
                        '"crs":{"type":"link","properties":' \
                        '{"href":"http://spatialreference.org/ref/epsg/4326/proj4/","type":"proj4"}}}]}'
        geojson_value = mock.MagicMock()
        geojson_value.is_valid = False
        mock_geojson.loads.return_value = geojson_value

        try:
            SpatialInputMWV().parse_drawn_geometry(geometry_json)
            self.assertTrue(False)  # This line should not be reached
        except RuntimeError as e:
            self.assertIn('Invalid geojson from "geometry" parameter:', str(e))

    def test_combine_geojson_objects_shapefile_no_geometry(self):
        shapefile = ' '
        geometry = None

        ret = SpatialInputMWV().combine_geojson_objects(shapefile, geometry)

        self.assertEqual(shapefile, ret)

    def test_combine_geojson_objects_geometry_no_shapefile(self):
        shapefile = None
        geometry = ' '

        ret = SpatialInputMWV().combine_geojson_objects(shapefile, geometry)

        self.assertEqual(geometry, ret)

    def test_combine_geojson_objects_both(self):
        shapefile = {'features': [{'geometry': {'coordinates': [0, 5], 'type': 'some_type'}, 'properties': {}}]}
        geometry = {'features': [{'geometry': {'coordinates': [1, 6], 'type': 'other_type'}, 'properties': {'id': 7}}]}

        ret = SpatialInputMWV().combine_geojson_objects(shapefile, geometry)

        self.assertEqual(shapefile['features'][0], ret['features'][0])
        self.assertEqual(geometry['features'][0], ret['features'][1])

    def test_post_process_geojson_no_geojson(self):
        ret = SpatialInputMWV().post_process_geojson(None)

        self.assertEqual(ret, None)

    def test_post_process_geojson(self):
        geojson = {
            'features': [
                {'geometry': {'coordinates': [], 'type': 'some_type'}, 'properties': {}},
                {'geometry': {'coordinates': [], 'type': 'some_type'}, 'properties': {}}
            ]
        }

        ret = SpatialInputMWV().post_process_geojson(geojson)

        self.assertIn('type', ret)
        self.assertIn('crs', ret)
        self.assertIn('type', ret['crs'])
        self.assertIn('properties', ret['crs'])
        self.assertIn('features', ret)
        self.assertIn('type', ret['features'][0])
        self.assertIn('geometry', ret['features'][0])
        self.assertEqual(geojson['features'][0]['geometry']['type'], ret['features'][0]['geometry']['type'])
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'],
                         ret['features'][0]['geometry']['coordinates'])
        self.assertIn('properties', ret['features'][0])

    def test_post_process_geojson_sorting(self):
        # When sorted, the Point type should be first, then LineString, then Polygon
        geojson = {
            'features': [
                {'geometry': {'coordinates': [[-86.713342, 33.500775], [-86.704177, 33.507294]], 'type': 'LineString'},
                 'properties': {}},
                {'geometry': {'coordinates': [[[-86.655385, 33.532015],
                                               [-86.655385, 33.542351],
                                               [-86.629775, 33.542351],
                                               [-86.629775, 33.532015],
                                               [-86.655385, 33.532015]]], 'type': 'Polygon'},
                 'properties': {}},
                {'geometry': {'coordinates': [-87.718464, 33.49583], 'type': 'Point'}, 'properties': {}},
            ]
        }

        ret = SpatialInputMWV().post_process_geojson(geojson)

        self.assertIn('type', ret)
        self.assertIn('crs', ret)
        self.assertIn('type', ret['crs'])
        self.assertIn('properties', ret['crs'])
        self.assertIn('features', ret)
        self.assertIn('type', ret['features'][0])
        self.assertIn('geometry', ret['features'][0])
        self.assertIn('type', ret['features'][1])
        self.assertIn('geometry', ret['features'][1])
        self.assertIn('type', ret['features'][2])
        self.assertIn('geometry', ret['features'][2])
        # Make sure the Point (last feature in geojson) comes first in the return value
        self.assertEqual(geojson['features'][2]['geometry']['type'], ret['features'][0]['geometry']['type'])
        self.assertEqual(geojson['features'][2]['geometry']['coordinates'],
                         ret['features'][0]['geometry']['coordinates'])
        # Make sure the LineString (first feature in geojson) comes second in the return value
        self.assertEqual(geojson['features'][0]['geometry']['type'], ret['features'][1]['geometry']['type'])
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'],
                         ret['features'][1]['geometry']['coordinates'])
        # Make sure the Polygon (second feature in geojson) comes last in the return value
        self.assertEqual(geojson['features'][1]['geometry']['type'], ret['features'][2]['geometry']['type'])
        self.assertEqual(geojson['features'][1]['geometry']['coordinates'],
                         ret['features'][2]['geometry']['coordinates'])
        self.assertIn('properties', ret['features'][0])
        self.assertIn('properties', ret['features'][1])
        self.assertIn('properties', ret['features'][2])

    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_parse_shapefile_with_datesvalid(self, mock_get_app):
        mock_app = TethysAppBase()
        mock_app_path = mock.MagicMock()
        mock_app_path.path = self.shapefile_dir
        mock_app.get_user_workspace = mock.MagicMock(return_value=mock_app_path)
        mock_get_app.return_value = mock_app

        with open(self.TestDates4326_zip, 'rb') as f:
            shapefile = InMemoryUploadedFile(
                file=f,
                field_name='shapefile',
                name='TestDates4326.zip',
                content_type='application/zip',
                size=1040,
                charset=None
            )

            geojson = SpatialInputMWV().parse_shapefile(self.request, shapefile)

        self.assertIn('features', geojson)
        self.assertIn('type', geojson)
        self.assertEqual('FeatureCollection', geojson['type'])
        self.assertEqual(5, len(geojson['features']))
        self.assertIn('coordinates', geojson['features'][0]['geometry'])
        self.assertEqual('LineString', geojson['features'][0]['geometry']['type'])
        self.assertIn('properties', geojson['features'][0])
        self.assertIn('type', geojson['features'][0])
        self.assertIn('Date3', geojson['features'][0]['properties'])
        self.assertTrue(len(geojson['features'][0]['properties']['Date3']) > 0)

    @mock.patch.object(AppUsersViewMixin, 'get_app')
    def test_store_imagery(self, mock_get_app):
        layer_id = None
        mock_sm = mock.MagicMock()
        test_workspace_str = 'testing'
        mock_sm.WORKSPACE = test_workspace_str
        instance = SpatialInputMWV()

        # Test for a missing in memory file
        layer_id = instance.store_imagery(self.request, self.step1, None)
        self.assertEqual(None, layer_id)

        # Test for uploading a zip file to geoserver, as if it were an image, mocked
        instance._SpatialManager = mock_sm
        with open(self.BadProjection_zip, 'rb') as f:
            test_file = InMemoryUploadedFile(
                file=f,
                field_name='shapefile',
                name='BadProjection.zip',
                content_type='application/zip',
                size=955,
                charset=None
            )
            layer_id = instance.store_imagery(self.request, self.step1, test_file)
        self.assertTrue(layer_id.startswith(f'{test_workspace_str}:'))  # Starts with "<workspace name>:"
        self.assertTrue(layer_id.endswith('BadProjection'))  # Ends with base name of file

        # Test for an exception being raised
        exc_str = 'test exception'
        mock_get_app().get_spatial_dataset_service().create_coverage_layer.side_effect = [Exception(exc_str)]
        with self.assertRaises(RuntimeError) as cm:
            with open(self.BadProjection_zip, 'rb') as f:
                test_file = InMemoryUploadedFile(
                    file=f,
                    field_name='shapefile',
                    name='BadProjection.zip',
                    content_type='application/zip',
                    size=955,
                    charset=None
                )
                layer_id = instance.store_imagery(self.request, self.step1, test_file)
        self.assertEqual(f'An error has occurred while storing the GeoTiff: {exc_str}', str(cm.exception))
