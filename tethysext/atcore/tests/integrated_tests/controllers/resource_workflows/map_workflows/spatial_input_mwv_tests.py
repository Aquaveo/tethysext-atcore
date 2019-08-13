"""
********************************************************************************
* Name: spatial_input_mwv_tests.py
* Author: mlebaron
* Created On: August 6, 2016
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest, HttpResponseRedirect
from django.core.files.uploadedfile import InMemoryUploadedFile
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users import AppUser
from django.http import JsonResponse
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv import SpatialInputMWV
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


# class ChildResourceStep(ResourceWorkflowStep):
#
#     def init_parameters(self, *args, **kwargs):
#         self._parameters = {'geometry': {'value': None}}


class MapWorkflowViewTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.namespace = 'my_namespace'
        self.request.path = 'apps/and/such'

        self.context = {}

        self.workflow = ResourceWorkflow(name='foo')

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

        self.session.add(self.workflow)
        self.session.add(self.app_user)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_get_step_specific_context_has_active_role(self, _):
        self.step1.active_roles = []
        self.step1.options['allow_shapefile'] = False

        ret = SpatialInputMWV().get_step_specific_context(self.request, self.session, self.context, self.step1,
                                                          None, self.step2)

        self.assertEqual({'allow_shapefile': False}, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_get_step_specific_context_no_active_role(self, _, mock_user_has_active_role):
        mock_user_has_active_role.return_value = False
        self.step1.options['allow_shapefile'] = True

        ret = SpatialInputMWV().get_step_specific_context(self.request, self.session, self.context, self.step1,
                                                          None, self.step2)

        self.assertEqual({'allow_shapefile': False}, ret)

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    def test_process_step_options_no_attributes_nor_active_role(self, mock_user_role, mock_params, mock_get_managers):
        mock_user_role.return_value = False
        mock_params.return_value = {'geometry': 'shapes and such'}
        mock_get_managers.return_value = None, MapView()

        resource = mock.MagicMock()
        map_view = MapView()
        map_view.layers = []
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]

        SpatialInputMWV().process_step_options(self.request, self.session, self.context, resource, self.step1,
                                               None, self.step2)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.generate_django_form')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    def test_process_step_options_with_attributes_and_active_role(self, mock_user_role, mock_params, mock_get_managers,
                                                                  mock_form):
        mock_user_role.return_value = True
        mock_params.return_value = {'geometry': 'shapes and such'}
        mock_get_managers.return_value = None, MapView()
        mock_form.return_view = {}

        resource = mock.MagicMock()
        map_view = MapView()
        map_view.layers = []
        self.context['map_view'] = map_view
        self.context['layer_groups'] = [{}]
        self.step1.options['attributes'] = True

        SpatialInputMWV().process_step_options(self.request, self.session, self.context, resource, self.step1,
                                               None, self.step2)

    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    def test_process_step_options_unknown_shape(self, mock_user_role, mock_params, mock_get_managers):
        mock_user_role.return_value = True
        mock_params.return_value = {'geometry': 'shapes and such'}
        mock_get_managers.return_value = None, MapView()

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

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.set_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.SpatialInputMWV.parse_drawn_geometry')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.SpatialInputMWV.parse_shapefile')
    def test_process_step_data(self, mock_parse_shp, mock_parse_geom, _):
        mock_parse_shp.return_value = {'features': [{'geometry': {'coordinates': [0, 5], 'type': 'some_type'}, 'properties': {}}]}
        mock_parse_geom.return_value = {'features': [{'geometry': {'coordinates': [1, 6], 'type': 'other_type'}, 'properties': {'id': 7}}]}
        mock_db = mock.MagicMock(spec=ModelDatabase)
        self.request.POST = {'geometry': {'value': 'shapes'}}
        self.request.FILES = {'shapefile': 'Det1poly.shp'}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db, './current',
                                                       './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./current', response.url)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.set_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.SpatialInputMWV.parse_drawn_geometry')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_input_mwv.SpatialInputMWV.parse_shapefile')
    def test_process_step_data_no_shapefile(self, mock_parse_shp, mock_parse_geom, _):
        mock_parse_shp.return_value = {'features': [{'geometry': {'coordinates': [0, 5], 'type': 'some_type'}, 'properties': {}}]}
        mock_parse_geom.return_value = {'features': [{'geometry': {'coordinates': [1, 6], 'type': 'other_type'}, 'properties': {'id': 7}}]}
        mock_db = mock.MagicMock(spec=ModelDatabase)
        self.request.POST = {'geometry': {'value': 'shapes'}}
        self.request.FILES = {'shapefile': None}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db, './current',
                                                       './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./prev', response.url)

    def test_process_step_data_previous(self):
        mock_db = mock.MagicMock(spec=ModelDatabase)
        self.request.POST = {'geometry': None, 'previous-submit': True}
        self.request.FILES = {'shapefile': None}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db, './current',
                                                       './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./prev', response.url)

    def test_process_step_data_not_previous(self):
        mock_db = mock.MagicMock(spec=ModelDatabase)
        self.request.POST = {'geometry': None, 'next-submit': True}
        self.request.FILES = {'shapefile': None}
        self.step1._parameters = {'geometry': {'value': 'shapes'}}
        response = None

        try:
            response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db,
                                                           './current', './prev', './next')
        except ValueError as e:
            self.assertEqual('You must either draw at least one singular_name or upload a shapefile of my_plural_name.',
                             str(e))
            self.assertEqual({'geometry': {'value': None}}, self.step1._parameters)
            self.assertTrue(self.step1.dirty)
        self.assertTrue(response is None)

    # def test_validate_feature_attributes(self):
    #     self.request.POST = mock.MagicMock()
    #     # SpatialInputRWS steps
    #
    #     response = SpatialInputMWV().validate_feature_attributes(self.request, self.session, None, self.step1.id)
    #
    #     self.assertIsInstance(response, JsonResponse)
    #     breakpoint()

    def test_parse_shapefile_no_file(self):
        shapefile = None

        ret = SpatialInputMWV().parse_shapefile(self.request, shapefile)

        self.assertEqual(None, ret)

    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app')
    # def test_parse_shapefile(self, mock_get_app):
    #     mock_app = mock.MagicMock(spec=TethysAppBase)
    #     mock_app_path = mock.MagicMock()
    #     mock_app_path.path = '/home/mlebaron/src/tethysext-atcore/tethysext/atcore/tests/files/shapefile'
    #     mock_app.get_user_workspace.return_value = mock_app_path
    #     mock_get_app.return_value = mock_app
    #     # shapefile = InMemoryUploadedFile(
    #     #     file='/home/mlebaron/src/tethysext-atcore/tethysext/atcore/tests/files/shapefile/Det1poly.zip',
    #     #     field_name='',
    #     #     name='Det1poly.zip',
    #     #     content_type='',
    #     #     size=0,
    #     #     charset=''
    #     # )
    #     shapefile = mock.MagicMock()
    #     shapefile.file = '/home/mlebaron/src/tethysext-atcore/tethysext/atcore/tests/files/shapefile'
    #     shapefile.name = 'Det1poly.zip'
    #     shapefile.chunks.return_value = [b'stuff', b'more stuff']
    #
    #     SpatialInputMWV().parse_shapefile(self.request, shapefile)
    #     # chunks and not a zip

    def test_parse_shapefile_generic_exception(self):
        shapefile = InMemoryUploadedFile(
            file='/home/mlebaron/src/tethysext-atcore/tethysext/atcore/tests/files/shapefile/Det1poly.zip',
            field_name='',
            name='Det1poly.zip',
            content_type='',
            size=0,
            charset=''
        )

        try:
            SpatialInputMWV().parse_shapefile(self.request, shapefile)
            self.assertTrue(False) # This should not be reached
        except RuntimeError as e:
            self.assertIn('An error has occurred while parsing the shapefile:', str(e))

    # def test_parse_shapefile_no_shapefile(self):
    #     # Use files/shapefile/MissingSHP.zip
    #     try:
    #         SpatialInputMWV().parse_shapefile(self.request, shapefile)
    #         self.assertTrue(False) # This should not be reached
    #     except ValueError as e:
    #         self.assertEqual('No shapefile found in given files.', str(e))

    # def test_parse_shapefile_no_projection_file(self):
    #     # Use files/shapefile/MissingPrj.zip
    #     try:
    #         SpatialInputMWV().parse_shapefile(self.request, shapefile)
    #         self.assertTrue(False) # This should not be reached
    #     except ValueError as e:
    #         self.assertIn('Unable to determine projection of the given shapefile. Please include a .prj file.', str(e))

    def test_validate_projection_projcs(self):
        proj_str = 'data PROJCS data'

        try:
            SpatialInputMWV().validate_projection(proj_str)
            self.assertTrue(False) # This should not be reached
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

    # def test_parse_drawn_geometry_valid(self):
    #     geometry = '{"geometries":[{"properties":[]}]}'
    #
    #     ret = SpatialInputMWV().parse_drawn_geometry(geometry)
    #     # geojson_objs.geometries doesn't exist
    #     self.assertEqual(ret, None)

    # def test_parse_drawn_geometry_invalid(self):
    #     geometry = '{"geometries":[{"properties":[]}]}'
    #
    #     ret = SpatialInputMWV().parse_drawn_geometry(geometry)
    #     # geojson_objs.geometries doesn't exist
    #     self.assertEqual(ret, None)

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
                {'geometry': {'coordinates': []}}
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
