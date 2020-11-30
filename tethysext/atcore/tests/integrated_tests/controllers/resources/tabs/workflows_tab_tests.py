"""
********************************************************************************
* Name: workflows_tab_tests.py
* Author: nswain
* Created On: November 23, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""

from django.test import RequestFactory

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowsTabTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request_factory = RequestFactory()

        self.resource = Resource(
            name="Test Resource"
        )

        self.session.add(self.resource)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def test_properties_default(self):
        """Verify the default value of any properties of ResourceWorkflowsTab."""
        pass

    def test_get_workflow_types_default(self):
        """Verify the default behavior of the ResourceWorkflowsTab.get_workflow_types() method."""
        pass

    def test_get_map_manager_default(self):
        """Verify the default behavior of the ResourceWorkflowsTab.get_map_manager() method."""
        pass

    def test_get_spatial_manager_default(self):
        """Verify the default behavior of the ResourceWorkflowsTab.get_spatial_manager() method."""
        pass

    def test_get_sds_setting_name_default(self):
        """Verify the default behavior of the ResourceWorkflowsTab.get_sds_setting_name() method."""
        pass

    def test_get_tabbed_view_context(self):
        """Verify that the additional context provided by ResourceWorkflowsTab."""
        pass

    def test_get_context_default(self):
        """Verify call path with default values for properties and methods."""
        pass

    def test_get_context_show_all_workflows_user_role(self):
        """Test case when show_all_workflows is False but user has a role listed in show_all_workflows_roles."""
        pass

    def test_get_context_show_all_workflows_no_user_role(self):
        """Test case when show_all_workflows is True and user does not have a role listed in show_all_workflows_roles."""  # noqa: E501
        pass

    def test_get_context_user_workflows_only(self):
        """Test case when show_all_workflows is False and user does not have a role listed in show_all_workflows_roles."""  # noqa: E501
        pass

    def test_get_context_workflow_status_pending(self):
        """Verify workflow cards for workflow that has pending status."""
        pass

    def test_get_context_workflow_status_working(self):
        """Verify workflow cards for workflow that has working status."""
        pass

    def test_get_context_workflow_status_complete(self):
        """Verify workflow cards for workflow that has complete status."""
        pass

    def test_get_context_workflow_status_error(self):
        """Verify workflow cards for workflow that has error status."""
        pass

    def test_get_context_workflow_status_failed(self):
        """Verify workflow cards for workflow that has failed status."""
        pass

    def test_get_context_workflow_status_other(self):
        """Verify workflow cards for workflow that has some other status."""
        pass

    def test_get_context_user_is_creator(self):
        """Verify workflow cards for workflow that was created by current user."""
        pass

    def test_get_context_user_is_not_creator(self):
        """Verify workflow cards for workflow that was not created by current user."""
        pass

    def test_get_context_exception(self):
        """Verify that the session is closed if an exception occurs."""
        pass  # TODO: Is this necessary? Should be handled somewhere else.

    def test_post_ideal(self):
        """Test new workflow form submissions with ideal submission."""
        pass

    def test_post_new_workflow_not_in_params(self):
        """Test new workflow form submissions with missing new-workflow parameter."""
        pass

    def test_post_no_workflow_name(self):
        """Test new workflow form submissions with missing workflow name."""
        pass

    def test_post_no_workflow_type(self):
        """Test new workflow form submissions with missing workflow type."""
        pass

    def test_post_exception_during_model_creation(self):
        """Test new workflow form submissions with exception occurring during creation of the new workflow."""
        pass

    def test_delete_ideal(self):
        """Test delete workflows requests with ideal submission."""
        pass

    def test_delete_exception(self):
        """Test delete workflows requests with exception occurring."""
        pass
