"""
********************************************************************************
* Name: spatial_data_mwv_tests.py
* Author: mlebaron
* Created On: August 15, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_data_mwv import SpatialDataMWV
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.resource_workflow_steps.spatial_rws import SpatialResourceWorkflowStep
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialDataMwvTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        log_patcher = mock.patch('tethys_gizmos.gizmo_options.map_view.log')
        self.mock_log = log_patcher.start()
        self.addCleanup(log_patcher.stop)

        self.request = mock.MagicMock(spec=HttpRequest)
        self.resource = mock.MagicMock()
        self.resource.id = '12345'

        self.workflow = ResourceWorkflow(name='foo')

        self.step = SpatialResourceWorkflowStep(
            geoserver_name='geo_server',
            map_manager=mock.MagicMock(spec=MapManagerBase),
            spatial_manager=mock.MagicMock(),
            name='name1',
            help='help1',
            order=1
        )

        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def test_process_step_options_no_geometry_source(self):
        context = {}
        self.step.options = {'geometry_source': None}

        try:
            SpatialDataMWV().process_step_options(self.request, self.session, context, self.resource, self.step,
                                                  None, None)
            self.assertTrue(False)  # This step should not be reached
        except RuntimeError as e:
            self.assertEqual('The geometry option is required.', str(e))

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.MapWorkflowView.add_layers_for_previous_steps')  # noqa: E501
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_process_step_options_no_active_role_no_parent(self, mock_get_managers, mock_user_role,
                                                           mock_get_param, mock_add_layers):
        mock_get_managers.return_value = None, MapManagerBase(mock.MagicMock(), mock.MagicMock())
        mock_user_role.return_value = False
        mock_get_param.return_value = {'features': []}
        map_view = mock.MagicMock(spec=MapView)
        map_view.layers = []
        context = {'map_view': map_view, 'layer_groups': []}
        mock_add_layers.return_value = map_view, context['layer_groups']
        self.step.options = {'geometry_source': 'geometry', 'dataset_title': 'my_dataset'}

        SpatialDataMWV().process_step_options(self.request, self.session, context, self.resource, self.step,
                                              './prev', './next')

        self.assertIn('map_view', context)
        self.assertIn('layer_groups', context)
        self.assertIn('enable_properties_popup', context)
        self.assertIn('enable_spatial_data_popup', context)
        self.assertIn('can_run_workflows', context)
        self.assertEqual(self.step.options['dataset_title'],
                         context['map_view'].__dict__['layers'][0]['data']['popup_title'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.MapWorkflowView.add_layers_for_previous_steps')  # noqa: E501
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.user_has_active_role')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_managers')
    def test_process_step_options_yes_active_role_yes_parent(self, mock_get_managers, mock_user_role,
                                                             mock_get_param, mock_add_layers):
        mock_get_managers.return_value = None, MapManagerBase(mock.MagicMock(), mock.MagicMock())
        mock_user_role.return_value = True
        mock_get_param.return_value = {'features': []}
        map_view = mock.MagicMock(spec=MapView)
        map_view.layers = []
        context = {'map_view': map_view, 'layer_groups': []}
        mock_add_layers.return_value = map_view, context['layer_groups']

        step1 = mock.MagicMock(spec=SpatialResourceWorkflowStep)
        step1.options = {'singular_name': 'single_name'}
        step2 = mock.MagicMock(spec=SpatialResourceWorkflowStep)
        step2.options = {'geometry_source': 'geometry'}
        step2.parent = step1

        SpatialDataMWV().process_step_options(self.request, self.session, context, self.resource, step2,
                                              './prev', './next')

        self.assertIn('map_view', context)
        self.assertIn('layer_groups', context)
        self.assertIn('enable_properties_popup', context)
        self.assertIn('enable_spatial_data_popup', context)
        self.assertIn('can_run_workflows', context)
        self.assertEqual(step1.options['singular_name'],
                         context['map_view'].__dict__['layers'][0]['data']['popup_title'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')
    def test_get_popup_form(self, mock_get_workflow, mock_get_step):
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = self.step

        SpatialDataMWV().get_popup_form(self.request, self.workflow.id, self.step.id, back_url='./back',
                                        session=self.session, resource=self.resource)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')
    def test_save_spatial_data(self, mock_get_workflow, mock_get_step):
        mock_get_workflow.return_value = self.workflow
        mock_get_step.return_value = self.step

        SpatialDataMWV().save_spatial_data(self.request, self.workflow.id, self.step.id, back_url='./back',
                                           session=self.session, resource=self.resource)
