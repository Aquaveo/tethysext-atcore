from unittest import mock
from django.test import RequestFactory
from django.contrib.auth.models import User
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class WorkflowViewTests(SqlAlchemyTestCase):

    def setUp(self):
        self.workflow = mock.MagicMock()
        mock.MagicMock(

        )
        self.workflow.steps = []

    def tearDown(self):
        # super().tearDown()
        pass

    def test_get_context(self):
        pass

    def test_get_context_message(self):
        # Or without message
        # Fail, complete and other
        pass

    @mock.patch('tethys_apps.models.TethysApp')
    def test_get_step_url_name(self, mock_app):
        mock_app.objects.get.return_value = mock.MagicMock(namespace='my_workspace')
        mock_request = mock.MagicMock(path='apps/and/such')
        mock_workflow = mock.MagicMock(type='my_type')

        ret = ResourceWorkflowView().get_step_url_name(mock_request, mock_workflow)

        self.assertEqual('my_workspace:my_type_workflow_step', ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.build_step_cards.')
    def test_build_step_cards(self):
        pass
