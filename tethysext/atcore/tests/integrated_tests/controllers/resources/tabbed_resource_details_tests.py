"""
********************************************************************************
* Name: tabbed_resource_details_tests.py
* Author: nswain
* Created On: November 23, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from unittest import mock

from django.test import RequestFactory
from tethys_apps.models import TethysApp

from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
# from tethysext.atcore.controllers.resources import TabbedResourceDetails


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TabbedResourceDetailsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request_factory = RequestFactory()
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

        self.resource = Resource(
            name="test_organization"
        )

        self.session.add(self.resource)
        self.session.commit()

        self.app = mock.MagicMock(spec=TethysApp, namespace='app_namespace')

        messages_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.messages')  # noqa: E501
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        redirect_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.redirect')  # noqa: E501
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        reverse_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
        self.mock_mixins_reverse = reverse_mixins_patcher.start()
        self.addCleanup(reverse_mixins_patcher.stop)

        get_app_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.get_active_app')
        self.mock_get_mixins_app = get_app_mixins_patcher.start()
        self.mock_get_mixins_app.return_value = self.app
        self.addCleanup(get_app_mixins_patcher.stop)

        get_app_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.resource_workflow_router.get_active_app')  # noqa: E501
        self.mock_get_app = get_app_patcher.start()
        self.mock_get_app.return_value = self.app
        self.addCleanup(get_app_patcher.stop)

        session_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
        self.mock_get_session_maker = session_patcher.start()
        self.mock_get_session_maker.return_value = mock.MagicMock
        self.addCleanup(session_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def test_properties_default(self):
        """Verify the default value of any properties of TabbedResourceDetails."""
        pass

    def test_get_with_tab_action(self):
        """Test for GET requests that include the tab_action parameter. Should route to ResourceTab for handling."""
        pass

    def test_get_without_tab_action(self):
        """Test for GET requests without the tab_action parameter. Should render the TabbedResourceDetails page."""
        pass

    def test_post_with_tab_action(self):
        """Test for POST requests that include the tab_action parameter. Should route to ResourceTab for handling."""
        pass

    def test_post_without_tab_action(self):
        """Test for POST requests without the tab_action parameter. Should return a Method Not Allowed response."""
        pass

    def test_delete_with_tab_action(self):
        """Test for DELETE requests that include the tab_action parameter. Should route to ResourceTab for handling."""
        pass

    def test_delete_without_tab_action(self):
        """Test for DELETE requests without the tab_action parameter. Should return a Method Not Allowed response."""
        pass

    def test_handle_tab_action_request_no_tab(self):
        """Test case when given tab_slug doesn't match any ResourceTab. Should return a Not Found response."""
        pass

    def test_handle_tab_action_request_tab_action_default(self):
        """Test case when the tab_action is 'default'. Should call the ResourceTab view as a controller."""
        pass

    def test_handle_tab_action_request_tab_action_method_name(self):
        """Test case when tab_action is the name of a method on the ResourceTab view."""
        pass

    def test_handle_tab_action_request_tab_action_invalid_method_name(self):
        """Test case when tab_action is not 'default' and does not match any method on the Tab view."""
        pass

    def test_get_tab_view_tab_found(self):
        """Test case when a TabResource is found for the given tab_slug."""
        pass

    def test_get_tab_view_tab_not_found(self):
        """Test case when a TabResource cannot be found for the given tab_slug."""
        pass

    def test_build_static_requirements(self):
        """Test the base case build_static_requirement method."""
        pass

    def test_build_static_requirements_duplicate_css_from_self(self):
        """Test case when duplicate CSS requirement is provided by the TabbedResourceDetail view."""
        pass

    def test_build_static_requirements_duplicate_css_from_tab(self):
        """Test case when duplicate CSS requirement is provided by a ResourceTab view."""
        pass

    def test_build_static_requirements_duplicate_js_from_self(self):
        """Test case when duplicate JS requirement is provided by the TabbedResourceDetail view."""
        pass

    def test_build_static_requirements_duplicate_js_from_tab(self):
        """Test case when duplicate JS requirement is provided by a ResourceTab view."""
        pass

    def test_get_context_default(self):
        """Test default implementation of get_context."""
        pass

    def test_get_tabs_self_tabs_not_none(self):
        """Test case when self.tabs is defined."""
        pass

    def test_get_tabs_self_tabs_none(self):
        """Test case when self.tabs is not defined."""
        pass
