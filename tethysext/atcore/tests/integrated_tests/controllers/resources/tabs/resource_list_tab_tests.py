"""
********************************************************************************
* Name: resource_list_tab_tests.py
* Author: gagelarsen
* Created On: January 15, 2021
* Copyright: (c) Aquaveo 2021
********************************************************************************
"""
from unittest import mock

from django.test import RequestFactory

from tethysext.atcore.models.app_users import Resource, SpatialResource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resources import ResourceListTab


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceListTabTests(SqlAlchemyTestCase):

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

    @mock.patch('tethysext.atcore.controllers.resources.tabs.resource_list_tab.reverse')
    def test_get_context_default(self, mock_reverse):
        """Test get_context()"""
        instance = ResourceListTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()

        with mock.patch.object(ResourceListTab, 'get_resources') as mock_get_resources:
            model = SpatialResource()
            mock_get_resources.return_value = [model]
            instance._app = mock.MagicMock()
            context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('resources', context)
        self.assertEqual(len(context['resources']), 1)

    def test_get_no_resources(self):
        """Test get_context()"""
        instance = ResourceListTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()
        instance._app = mock.MagicMock()
        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('resources', context)
        self.assertEqual(len(context['resources']), 0)

    def test_get_resources(self):
        """Test get_resources()"""
        instance = ResourceListTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        resources = instance.get_resources(request, None, None)
        self.assertEqual(len(resources), 0)

    @mock.patch('tethysext.atcore.controllers.resources.tabs.resource_list_tab.reverse')
    def test_build_resource_cards(self, reverse_mock):
        """Test _build_resource_cards()"""
        instance = ResourceListTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()

        model = SpatialResource()
        resources = [model]
        reverse_mock.return_value = 'mock_href'
        instance._app = mock.MagicMock()
        cards = instance._build_resource_cards(resources)

        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['action'], 'launch')
        self.assertEqual(cards[0]['action_title'], 'View Resource')
        self.assertEqual(cards[0]['action_href'], 'mock_href')
