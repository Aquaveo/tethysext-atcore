"""
********************************************************************************
* Name: summary_tab_tests.py
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
# from tethysext.atcore.controllers.resources import ResourceSummaryTab


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


# noinspection PyAttributeOutsideInit
class ResourceSummaryTabTests(SqlAlchemyTestCase):

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

        self.summary_info = [
            [
                ('Foo Title', {'int': 1}),
                ('Bar Title', {'float': 10.0, 'str': 'Foo'}),
            ],
            [
                ('Baz Title', {'bool': True}),
            ],
        ]

        self.app = mock.MagicMock(spec=TethysApp, namespace='app_namespace')

        messages_patcher = mock.patch(
            'tethysext.atcore.controllers.resource_workflows.resource_workflow_router.messages')  # noqa: E501
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        redirect_patcher = mock.patch(
            'tethysext.atcore.controllers.resource_workflows.resource_workflow_router.redirect')  # noqa: E501
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        reverse_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.reverse')
        self.mock_mixins_reverse = reverse_mixins_patcher.start()
        self.addCleanup(reverse_mixins_patcher.stop)

        get_app_mixins_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.get_active_app')
        self.mock_get_mixins_app = get_app_mixins_patcher.start()
        self.mock_get_mixins_app.return_value = self.app
        self.addCleanup(get_app_mixins_patcher.stop)

        get_app_patcher = mock.patch(
            'tethysext.atcore.controllers.resource_workflows.resource_workflow_router.get_active_app')  # noqa: E501
        self.mock_get_app = get_app_patcher.start()
        self.mock_get_app.return_value = self.app
        self.addCleanup(get_app_patcher.stop)

        session_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
        self.mock_get_session_maker = session_patcher.start()
        self.mock_get_session_maker.return_value = mock.MagicMock
        self.addCleanup(session_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def test_default_properties(self):
        """Verify the default values for the properties of the view."""
        pass

    def test_default_get_preview_image_url(self):
        """Test default implementation of get_preview_image_url."""
        pass

    def test_default_get_summary_tab_info(self):
        """Test default implementation of get_summary_tab_info."""
        pass

    def test_load_summary_tab_preview_image(self):
        pass

    def test_default_get_context(self):
        """Test get_context() with default implementation: no preview image, no summary tab info, user not staff."""
        pass

    def test_get_context_preview_image(self):
        """Test get_context() with only preview image defined."""
        pass

    def test_get_context_summary_tab_info(self):
        """Test get_context() with only summary tab info defined."""
        pass

    def test_get_context_preview_image_and_summary_tab_info(self):
        """Test get_context() with preview image and summary tab info defined."""
        pass

    def test_get_context_staff_user(self):
        """Test that debug information is generated for staff users."""
        pass

    def test_get_context_staff_user_resource_locked_for_specific_user(self):
        """
        Test that username with user lock is displayed in debug information
        when resource is locked by a specific user.
        """
        pass

    def test_get_context_staff_user_resource_locked_for_all_users(self):
        """Test that "All Users" is displayed in debug information when resource is locked for all users."""
        pass
