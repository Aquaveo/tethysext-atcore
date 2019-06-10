"""
********************************************************************************
* Name: base.py
* Author: Tanner, Teva
* Created On: December  14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import datetime as dt
from unittest import mock
from tethys_sdk.base import TethysController
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.models.app_users import ResourceWorkflow, AppUser, Resource
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.spatial_manager import SpatialManager
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView, \
    AppUsersResourceController
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TestController(TethysController):
    pass


class AppUsersResourceWorkflowControllerTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.user = AppUser(
            username="user1",
            role=Roles.ORG_USER,
        )
        self.session.add(self.user)

        self.pre_created_date = dt.datetime.utcnow()

        # create resource
        self.resource = Resource(
            name='eggs',
            description='for eating',
        )

        self.session.add(self.resource)

        # create resource workflow
        self.workflow_name = "test_workflow"
        self.resource_workflow = ResourceWorkflow(
            name=self.workflow_name,
            creator=self.user,
            resource=self.resource
        )

        # add the workflow to the session after adding the steps
        self.session.add(self.resource_workflow)

        self.resource_id = self.resource.id

        # create resource workflow steps
        self.geoserver_name = ''
        self.spatial_manager = SpatialManager(object())
        self.map_manager = MapManagerBase(self.spatial_manager, object())

        # Define the steps
        step = ResourceWorkflowStep(
            name='Test_workflow_steps',
            help='Test workflow help.',
            controller_path='tethysext.atcore.tests.integrated_tests.controllers.'
                            'resource_workflows.base.TestController',
            controller_kwargs={
                'geoserver_name': self.geoserver_name,
                '_MapManager': self.map_manager,
                '_SpatialManager': self.spatial_manager
            }
        )

        self.resource_workflow.steps.append(step)

        self.session.commit()

    def test_get_app(self):
        app_user_resource_workflow = ResourceWorkflowView()
        self.assertIsNone(app_user_resource_workflow.get_app())

    def test_get_app_user_model(self):
        app_user_resource_workflow = ResourceWorkflowView()
        Res = app_user_resource_workflow.get_app_user_model()
        a = self.session.query(Res).all()
        self.assertEqual('user1', a[0].username)
        self.assertEqual(Roles.ORG_USER, a[0].role)

    def test_get_organization_model(self):
        app_user_resource_workflow = ResourceWorkflowView()
        Res = app_user_resource_workflow.get_organization_model()
        self.assertEqual(Organization, Res)

    def test_get_resource_model(self):
        app_user_resource_workflow = ResourceWorkflowView()
        Res = app_user_resource_workflow.get_resource_model()
        a = self.session.query(Res).all()
        self.assertEqual('eggs', a[0].name)
        self.assertEqual('for eating', a[0].description)
        self.assertEqual(Res, type(self.resource))

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin._app')
    def test_get_permission_manager(self, _):
        app_user_resource_workflow = ResourceWorkflowView()
        Res = app_user_resource_workflow.get_permissions_manager()
        self.assertIsInstance(Res, AppPermissionsManager)
        # TODO: Nathan is that good enough or should we create a permission manager

    def test_get_session_maker(self):
        app_user_resource_workflow = ResourceWorkflowView()
        self.assertRaises(NotImplementedError,  app_user_resource_workflow.get_sessionmaker)


class AppUsersResourceControllerTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()

        self.user = AppUser(
            username="user1",
            role=Roles.ORG_USER,
        )
        self.session.add(self.user)

        self.pre_created_date = dt.datetime.utcnow()

        # create resource
        self.resource = Resource(
            name='eggs',
            description='for eating',
        )

        self.session.add(self.resource)

        # create resource workflow
        self.workflow_name = "test_workflow"
        self.resource_workflow = ResourceWorkflow(
            name=self.workflow_name,
            creator=self.user,
            resource=self.resource
        )

        # add the workflow to the session after adding the steps
        self.session.add(self.resource_workflow)

        self.session.commit()

        self.resource_id = self.resource.id

        # create resource workflow steps
        self.geoserver_name = ''
        self.spatial_manager = SpatialManager(object())
        self.map_manager = MapManagerBase(self.spatial_manager, object())

        # Define the steps
        step = ResourceWorkflowStep(
            name='Test_workflow_steps',
            help='Test workflow help.',
            controller_path='tethysext.atcore.tests.integrated_tests.controllers.'
                            'resource_workflows.base.TestController',
            controller_kwargs={
                'geoserver_name': self.geoserver_name,
                '_MapManager': self.map_manager,
                '_SpatialManager': self.spatial_manager
            }
        )

        self.resource_workflow.steps.append(step)

    def test_dispatch(self):
        app_user_resource_workflow = ResourceWorkflowView()
        self.assertIsNone(app_user_resource_workflow.get_app())

    def test_default_back_url(self):
        pass

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_resource_model')
    def test_get_resource(self, _, mock_app_user, mock_session):
        app_user_resource_controller = AppUsersResourceController()
        mock_request = mock.MagicMock()

        mock_app_user().get_app_user_from_request.can_view.return_value = True

        session = mock_session()()

        resource_out = mock.MagicMock()

        session.query().filter().one.return_value = resource_out

        # call the method
        ret = app_user_resource_controller.get_resource(mock_request, self.resource_id)

        # test the results
        self.assertEqual(resource_out, ret)
        session.close.asset_called()

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_resource_model')
    def test_get_resource_can_view_atcore_exception(self, mock_resource, mock_app_user, mock_session, mock_redirect,
                                                    mock_messages):
        mock_request = mock.MagicMock()

        mock_request_app_user = mock_app_user().get_app_user_from_request()

        mock_request_app_user.can_view.return_value = False

        session = mock_session()()

        mock_resource().DISPLAY_TYPE_SINGULAR.lower.return_value = 'test_out'

        mock_redirect.return_value = 'foo/bar/baz'

        # call the method
        app_user_resource_controller = AppUsersResourceController()
        ret = app_user_resource_controller.get_resource(mock_request, self.resource_id)

        msg_warning_call_args = mock_messages.warning.call_args_list
        self.assertEqual('You are not allowed to access this test_out', msg_warning_call_args[0][0][1])
        self.assertEqual('foo/bar/baz', ret)
        session.close.assert_called()
        mock_redirect.assert_called()

    # TODO: Finish up the following test

    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.messages')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.redirect')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_resource_model')
    # def test_get_resource_can_view_statement_error(self, mock_resource, mock_app_user, mock_session, mock_redirect,
    #                                                mock_messages):
    #     import pdb
    #     pdb.set_trace()
    #
    #     from sqlalchemy.exc import StatementError
    #
    #     mock_request = mock.MagicMock()
    #
    #     mock_request_app_user = mock_app_user().get_app_user_from_request()
    #
    #     mock_request_app_user.can_view.return_value = True
    #
    #     mock_resource().DISPLAY_TYPE_SINGULAR.lower.return_value = 'test_out'
    #
    #     session = mock_session()()
    #
    #     session.query().filter().one().return_value = StatementError
    #
    #     mock_redirect.return_value = 'foo/bar/baz'
    #
    #     # call the method
    #     app_user_resource_controller = AppUsersResourceController()
    #     ret = app_user_resource_controller.get_resource(mock_request, self.resource_id)
    #
    #     import pdb
    #     pdb.set_trace()
    #     msg_warning_call_args = mock_messages.warning.call_args_list
    #     self.assertEqual('The test_out could not be found', msg_warning_call_args[0][0][1])
    #     self.assertEqual('foo/bar/baz', ret)
    #     session.close.assert_called()
    #     mock_redirect.assert_called()
