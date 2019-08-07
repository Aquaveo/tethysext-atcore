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

        self.session.add(self.workflow)
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

        with self.assertRaises(RuntimeError) as e:
            SpatialInputMWV().process_step_options(self.request, self.session, self.context, resource, self.step1,
                                                   None, self.step2)
            self.assertEqual('Invalid shapes defined: unknown_shape.', e.exception.message)

    # def test_process_step_data(self):
    #     mock_db = mock.MagicMock(spec=ModelDatabase)
    #     self.request.POST = {'geometry': 'something'}
    #
    #     response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db, './current',
    #                                                    './prev', './next')
    #
    #     self.assertEqual({}, response)

    def test_process_step_data_previous(self):
        mock_db = mock.MagicMock(spec=ModelDatabase)
        self.request.POST = {'geometry': None, 'previous-submit': True}
        self.request.FILES = {'shapefile': None}

        response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db, './current',
                                                       './prev', './next')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('./prev', response.url)

    # def test_process_step_data_not_previous(self):
    #     mock_db = mock.MagicMock(spec=ModelDatabase)
    #     self.request.POST = {'geometry': None, 'next-submit': True}
    #     self.request.FILES = {'shapefile': None}
    #
    #     response = SpatialInputMWV().process_step_data(self.request, self.session, self.step1, mock_db, './current',
    #                                                    './prev', './next')
    #
    #     self.assertIsInstance(response, HttpResponseRedirect)
    #     self.assertEqual('./prev', response.url)

    def test_parse_shapefile_no_file(self):
        in_memory_file = None

        ret = SpatialInputMWV().parse_shapefile(self.request, in_memory_file)

        self.assertEqual(None, ret)
