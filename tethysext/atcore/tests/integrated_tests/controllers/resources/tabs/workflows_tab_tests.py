"""
********************************************************************************
* Name: workflows_tab_tests.py
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
# from tethysext.atcore.controllers.resources import ResourceWorkflowsTab


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowsTabTests(SqlAlchemyTestCase):

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

    def test_foo(self):
        self.assertTrue(True)
