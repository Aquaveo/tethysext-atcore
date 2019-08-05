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
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view import MapWorkflowView
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.services.app_users.roles import Roles
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
        self.model_db = mock.MagicMock(spec=ModelDatabase)
        self.workflow = ResourceWorkflow(name='foo')

        self.step1 = ResourceWorkflowStep(
            name='name1',
            help='help1',
        )

        self.workflow.steps.append(self.step1)
        self.step2 = ResourceWorkflowStep(
            name='name2',
            help='help2',
        )

        self.workflow.steps.append(self.step2)
        self.step3 = ResourceWorkflowStep(
            name='name3',
            help='help3',
        )
        self.workflow.steps.append(self.step3)

        self.mock_map_manager = mock.MagicMock(spec=MapManagerBase)
        self.mock_map_manager().compose_map.return_value = (
            mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        )
        self.controller = MapWorkflowView.as_controller(
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

        self.session.add(self.workflow)
        self.session.add(self.app_user)
        self.session.commit()
        self.request_factory = RequestFactory()

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_adjacent_steps')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.on_get')
    @mock.patch('tethysext.atcore.controllers.map_view.MapView.get_resource')
    @mock.patch('tethysext.atcore.controllers.resource_view.render')
    @mock.patch('tethysext.atcore.controllers.map_view.has_permission')
    def test_get_context(self, mock_has_permission, mock_render, _, mock_on_get, mock_get_adj_steps):
        mock_on_get.return_value = None
        mock_get_adj_steps.return_value = mock.MagicMock(), mock.MagicMock()
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user
        resource = mock.MagicMock()

        response = self.controller(request=mock_request, resource_id=self.resource_id, back_url='./back_url',
                                   workflow_id=self.workflow.id, step_id=self.step1.id)
        #
        # response = self.controller(request=mock_request, session=self.session, resource=resource, context={},
        #                            model_db=mock.MagicMock(), workflow_id=self.workflow.id, step_id=self.step1.id,
        #                            back_url='./back_url')

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
