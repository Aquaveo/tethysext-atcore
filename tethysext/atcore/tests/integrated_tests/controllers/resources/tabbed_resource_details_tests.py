"""
********************************************************************************
* Name: tabbed_resource_details_tests.py
* Author: nswain
* Created On: November 23, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import copy
from unittest import mock

from django.test import RequestFactory
from django.http import HttpResponseNotAllowed, HttpResponseNotFound, HttpResponseBadRequest
from tethys_apps.models import TethysApp

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resources import ResourceTab, TabbedResourceDetails


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TestTab1(ResourceTab):
    css_requirements = ['atcore/app_users/css/resource_details.css', 'foo.css', 'bar.css']  # with duplicate from TRD

    def custom_action(self, *args, **kwargs):
        return 'TestTab1.custom_action returned'


class TestTab2(ResourceTab):
    js_requirements = ['atcore/js/lazy_load_tabs.js', 'foo.js', 'bar.js']  # with duplicate from TRD

    @classmethod
    def get_tabbed_view_context(cls, request, context):
        return {'another_item': 'baz'}


class TestTabbedResourceDetails(TabbedResourceDetails):

    tabs = [{'slug': 'a-tab', 'title': 'A Tab', 'view': TestTab1},
            {'slug': 'another-tab', 'title': 'Another Tab', 'view': TestTab2}]


class TabbedResourceDetailsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request_factory = RequestFactory()

        self.resource = Resource(
            name="Test Resource"
        )

        self.session.add(self.resource)
        self.session.commit()

        self.app = mock.MagicMock(spec=TethysApp, namespace='app_namespace')

        render_patcher = mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        self.mock_make_session = mock.MagicMock(return_value=self.session)
        get_sessionmaker_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin'
                                              '.get_sessionmaker')
        self.mock_get_sessionmaker = get_sessionmaker_patcher.start()
        self.mock_get_sessionmaker.return_value = self.mock_make_session
        self.addCleanup(get_sessionmaker_patcher.stop)

        get_resource_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin'
                                          '.get_resource')
        self.mock_get_resource = get_resource_patcher.start()
        self.mock_get_resource.return_value = self.resource
        self.addCleanup(get_resource_patcher.stop)

        has_permission_mixin_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.has_permission')
        self.mock_has_permission_mixin = has_permission_mixin_patcher.start()
        self.mock_has_permission_mixin.return_value = True
        self.addCleanup(has_permission_mixin_patcher.stop)

        # Patch the has_permission function in the permission_required decorator,
        # since we can't easily patch the decorator directly.
        has_permission_decorator_patcher = mock.patch('tethys_apps.decorators.has_permission')
        self.mock_has_permission_decorator = has_permission_decorator_patcher.start()
        self.mock_has_permission_decorator.return_value = True
        self.addCleanup(has_permission_decorator_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def get_request_with_user(self, url, request_type='get', data=None, is_staff=False, user_role=Roles.ORG_USER):
        """Helper function that creates a request with an active AppUser."""
        user = self.get_user(is_staff=is_staff, user_role=user_role)
        request = getattr(self.request_factory, request_type, 'get')(url, data)
        request.user = user
        return request

    def test_properties_default(self):
        """Verify the default value of any properties of TabbedResourceDetails."""
        self.assertEqual('atcore/resources/tabbed_resource_details.html', TabbedResourceDetails.template_name)
        self.assertIn('get', TabbedResourceDetails.http_method_names)
        self.assertIn('post', TabbedResourceDetails.http_method_names)
        self.assertIn('delete', TabbedResourceDetails.http_method_names)
        self.assertIn('atcore/js/enable-tabs.js', TabbedResourceDetails.js_requirements)
        self.assertIn('atcore/js/csrf.js', TabbedResourceDetails.js_requirements)
        self.assertIn('atcore/js/lazy_load_tabs.js', TabbedResourceDetails.js_requirements)
        self.assertIn('atcore/css/center.css', TabbedResourceDetails.css_requirements)
        self.assertIn('atcore/app_users/css/app_users.css', TabbedResourceDetails.css_requirements)
        self.assertIn('atcore/app_users/css/resource_details.css', TabbedResourceDetails.css_requirements)
        self.assertIsNone(TabbedResourceDetails.tabs)

    @mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.TabbedResourceDetails.'
                '_handle_tab_action_request')
    def test_get_with_tab_action(self, mock_htar):
        """Test for GET requests that include the tab_action parameter. Should route to ResourceTab for handling."""
        tab_slug = 'a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})  # Include tab_action parameter

        ret = instance.get(request, resource_id=str(self.resource.id), back_url='/foo/', tab_slug=tab_slug)

        mock_htar.assert_called_with(
            request=request, resource=self.resource, session=self.session, tab_slug=tab_slug, tab_action='default'
        )
        self.assertEqual(mock_htar(), ret)

    @mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.TabbedResourceDetails.'
                '_handle_tab_action_request')
    def test_get_without_tab_action(self, mock_htar):
        """Test for GET requests without the tab_action parameter. Should render the TabbedResourceDetails page."""
        tab_slug = 'a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get')  # No tab_action

        ret = instance.get(request, resource_id=str(self.resource.id), back_url='/foo/', tab_slug=tab_slug)

        mock_htar.assert_not_called()

        expected_context = {
            'resource': self.resource,
            'back_url': '',
            'base_template': 'atcore/app_users/base.html',
            'tabs': TestTabbedResourceDetails.tabs,
            'active_tab': tab_slug,
            'css_requirements': ['atcore/css/center.css', 'atcore/app_users/css/app_users.css',
                                 'atcore/app_users/css/resource_details.css',  # not duplicated
                                 'foo.css', 'bar.css'],  # from TestTab1
            'js_requirements': ['atcore/js/enable-tabs.js', 'atcore/js/csrf.js',
                                'atcore/js/lazy_load_tabs.js',  # not duplicated
                                'foo.js', 'bar.js'],  # from TestTab2
            'another_item': 'baz'  # from TestTab2
        }

        self.mock_render.assert_called_with(
            request,
            TestTabbedResourceDetails.template_name,
            expected_context
        )
        self.assertEqual(self.mock_render(), ret)

    @mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.TabbedResourceDetails.'
                '_handle_tab_action_request')
    def test_post_with_tab_action(self, mock_htar):
        """Test for POST requests that include the tab_action parameter. Should route to ResourceTab for handling."""
        tab_slug = 'a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'post',
                                             {'tab_action': 'default'})  # Include tab_action parameter

        ret = instance.post(request, resource_id=str(self.resource.id), back_url='/foo/', tab_slug=tab_slug)

        mock_htar.assert_called_with(
            request=request, resource=self.resource, tab_slug=tab_slug, tab_action='default'
        )
        self.assertEqual(mock_htar(), ret)

    @mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.TabbedResourceDetails.'
                '_handle_tab_action_request')
    def test_post_without_tab_action(self, mock_htar):
        """Test for POST requests without the tab_action parameter. Should return a Method Not Allowed response."""
        tab_slug = 'a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'post')  # No tab_action

        ret = instance.post(request, resource_id=str(self.resource.id), back_url='/foo/', tab_slug=tab_slug)

        mock_htar.assert_not_called()
        self.assertIsInstance(ret, HttpResponseNotAllowed)
        self.assertEqual('GET', ret['Allow'])

    @mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.TabbedResourceDetails.'
                '_handle_tab_action_request')
    def test_delete_with_tab_action(self, mock_htar):
        """Test for DELETE requests that include the tab_action parameter. Should route to ResourceTab for handling."""
        tab_slug = 'a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/?tab_action=default',
                                             'delete')  # Include tab_action parameter

        ret = instance.delete(request, resource_id=str(self.resource.id), back_url='/foo/', tab_slug=tab_slug)

        mock_htar.assert_called_with(
            request=request, resource=self.resource, tab_slug=tab_slug, tab_action='default'
        )
        self.assertEqual(mock_htar(), ret)

    @mock.patch('tethysext.atcore.controllers.resources.tabbed_resource_details.TabbedResourceDetails.'
                '_handle_tab_action_request')
    def test_delete_without_tab_action(self, mock_htar):
        """Test for DELETE requests without the tab_action parameter. Should return a Method Not Allowed response."""
        tab_slug = 'a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'delete')  # No tab_action

        ret = instance.delete(request, resource_id=str(self.resource.id), back_url='/foo/', tab_slug=tab_slug)

        mock_htar.assert_not_called()
        self.assertIsInstance(ret, HttpResponseNotAllowed)
        self.assertEqual('GET', ret['Allow'])

    def test_handle_tab_action_request_no_tab(self):
        """Test case when given tab_slug doesn't match any ResourceTab. Should return a Not Found response."""
        tab_slug = 'not-a-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})  # Include tab_action parameter

        ret = instance._handle_tab_action_request(request, self.resource, self.session, tab_slug, tab_action='default')

        self.assertIsInstance(ret, HttpResponseNotFound)
        self.assertEqual(b'"not-a-tab" is not a valid tab.', ret.content)

    def test_handle_tab_action_request_tab_action_default(self):
        """Test case when the tab_action is 'default'. Should call the ResourceTab view as a controller."""
        # Add a mocked ResourceTab so we can test what methods are called
        MockTab = mock.MagicMock(spec=ResourceTab)
        TestTabbedResourceDetails.tabs.append(
            {'slug': 'mock-tab', 'title': 'Mock Tab', 'view': MockTab}
        )
        instance = TestTabbedResourceDetails()
        tab_slug = 'mock-tab'  # use the MockTab tab
        tab_action = 'default'  # "default" action
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': tab_action})

        ret = instance._handle_tab_action_request(request, self.resource, self.session, tab_slug, tab_action=tab_action)

        MockTab.assert_not_called()  # ResourceTab not instantiated
        MockTab.as_controller.assert_called()  # Controller entry point was retrieved
        mock_tab_controller = MockTab.as_controller()
        self.assertEqual(mock_tab_controller(), ret)

    def test_handle_tab_action_request_tab_action_method_name(self):
        """Test case when tab_action is the name of a method on the ResourceTab view."""
        instance = TestTabbedResourceDetails()
        tab_slug = 'a-tab'  # use the MockTab tab
        tab_action = 'custom-action'  # use a method called custom_action
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': tab_action})

        ret = instance._handle_tab_action_request(request, self.resource, self.session, tab_slug, tab_action=tab_action)

        self.assertEqual('TestTab1.custom_action returned', ret)

    def test_handle_tab_action_request_tab_action_invalid_method_name(self):
        """Test case when tab_action is not 'default' and does not match any method on the Tab view."""
        # Add a mocked ResourceTab so we can test what methods are called
        instance = TestTabbedResourceDetails()
        tab_slug = 'another-tab'
        tab_action = 'not-a-method'  # not a valid action
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': tab_action})

        ret = instance._handle_tab_action_request(request, self.resource, self.session, tab_slug, tab_action=tab_action)

        self.assertIsInstance(ret, HttpResponseBadRequest)
        self.assertEqual(b'"not-a-method" is not a valid action for tab "another-tab"', ret.content)

    def test_get_tab_view_tab_found(self):
        """Test case when a TabResource is found for the given tab_slug."""
        tab_slug = 'another-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})

        ret = instance.get_tab_view(request, self.resource, tab_slug)

        self.assertIs(ret, TestTab2)

    def test_get_tab_view_tab_not_found(self):
        """Test case when a TabResource cannot be found for the given tab_slug."""
        tab_slug = 'bad-tab'
        instance = TestTabbedResourceDetails()
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})

        ret = instance.get_tab_view(request, self.resource, tab_slug)

        self.assertIsNone(ret)

    def test_build_static_requirements(self):
        """Test the base case build_static_requirement method."""
        class NoDuplicatesTrd(TabbedResourceDetails):
            css_requirements = ['foo.css', 'bar.css']
            js_requirements = ['foo.js', 'bar.js']

        class NoDuplicatesTab1(ResourceTab):
            css_requirements = ['foo1.css', 'bar1.css']
            js_requirements = ['foo1.js', 'bar1.js']

        class NoDuplicatesTab2(ResourceTab):
            css_requirements = ['foo2.css', 'bar2.css']
            js_requirements = ['foo2.js', 'bar2.js']

        instance = NoDuplicatesTrd()
        tabs = ({'slug': 'a-tab', 'title': 'A Tab', 'view': NoDuplicatesTab1},
                {'slug': 'another-tab', 'title': 'Another Tab', 'view': NoDuplicatesTab2})

        ret = instance.build_static_requirements(tabs)

        self.assertEqual(2, len(ret))
        self.assertListEqual(['foo.css', 'bar.css', 'foo1.css', 'bar1.css', 'foo2.css', 'bar2.css'], ret[0])
        self.assertListEqual(['foo.js', 'bar.js', 'foo1.js', 'bar1.js', 'foo2.js', 'bar2.js'], ret[1])

    def test_build_static_requirements_duplicate_css_from_self(self):
        """Test case when duplicate CSS requirement is provided by the TabbedResourceDetail view."""
        class DuplicateCssTrd(TabbedResourceDetails):
            css_requirements = ['foo.css', 'bar.css', 'foo.css']
            js_requirements = ['foo.js', 'bar.js']

        class NoDuplicatesTab1(ResourceTab):
            css_requirements = ['foo1.css', 'bar1.css']
            js_requirements = ['foo1.js', 'bar1.js']

        class NoDuplicatesTab2(ResourceTab):
            css_requirements = ['foo2.css', 'bar2.css']
            js_requirements = ['foo2.js', 'bar2.js']

        instance = DuplicateCssTrd()
        tabs = ({'slug': 'a-tab', 'title': 'A Tab', 'view': NoDuplicatesTab1},
                {'slug': 'another-tab', 'title': 'Another Tab', 'view': NoDuplicatesTab2})

        ret = instance.build_static_requirements(tabs)

        self.assertEqual(2, len(ret))
        self.assertListEqual(['foo.css', 'bar.css', 'foo1.css', 'bar1.css', 'foo2.css', 'bar2.css'], ret[0])
        self.assertListEqual(['foo.js', 'bar.js', 'foo1.js', 'bar1.js', 'foo2.js', 'bar2.js'], ret[1])

    def test_build_static_requirements_duplicate_css_from_tab(self):
        """Test case when duplicate CSS requirement is provided by a ResourceTab view."""
        class NoDuplicatesTrd(TabbedResourceDetails):
            css_requirements = ['foo.css', 'bar.css']
            js_requirements = ['foo.js', 'bar.js']

        class NoDuplicatesTab1(ResourceTab):
            css_requirements = ['foo1.css', 'bar1.css']
            js_requirements = ['foo1.js', 'bar1.js']

        class DuplicateCssTab(ResourceTab):
            css_requirements = ['foo2.css', 'bar2.css', 'foo1.css']
            js_requirements = ['foo2.js', 'bar2.js']

        instance = NoDuplicatesTrd()
        tabs = ({'slug': 'a-tab', 'title': 'A Tab', 'view': NoDuplicatesTab1},
                {'slug': 'another-tab', 'title': 'Another Tab', 'view': DuplicateCssTab})

        ret = instance.build_static_requirements(tabs)

        self.assertEqual(2, len(ret))
        self.assertListEqual(['foo.css', 'bar.css', 'foo1.css', 'bar1.css', 'foo2.css', 'bar2.css'], ret[0])
        self.assertListEqual(['foo.js', 'bar.js', 'foo1.js', 'bar1.js', 'foo2.js', 'bar2.js'], ret[1])

    def test_build_static_requirements_duplicate_js_from_self(self):
        """Test case when duplicate JS requirement is provided by the TabbedResourceDetail view."""
        class DuplicateJsTrd(TabbedResourceDetails):
            css_requirements = ['foo.css', 'bar.css']
            js_requirements = ['foo.js', 'bar.js', 'foo.js']

        class NoDuplicatesTab1(ResourceTab):
            css_requirements = ['foo1.css', 'bar1.css']
            js_requirements = ['foo1.js', 'bar1.js']

        class NoDuplicatesTab2(ResourceTab):
            css_requirements = ['foo2.css', 'bar2.css']
            js_requirements = ['foo2.js', 'bar2.js']

        instance = DuplicateJsTrd()
        tabs = ({'slug': 'a-tab', 'title': 'A Tab', 'view': NoDuplicatesTab1},
                {'slug': 'another-tab', 'title': 'Another Tab', 'view': NoDuplicatesTab2})

        ret = instance.build_static_requirements(tabs)

        self.assertEqual(2, len(ret))
        self.assertListEqual(['foo.css', 'bar.css', 'foo1.css', 'bar1.css', 'foo2.css', 'bar2.css'], ret[0])
        self.assertListEqual(['foo.js', 'bar.js', 'foo1.js', 'bar1.js', 'foo2.js', 'bar2.js'], ret[1])

    def test_build_static_requirements_duplicate_js_from_tab(self):
        """Test case when duplicate JS requirement is provided by a ResourceTab view."""
        class NoDuplicatesTrd(TabbedResourceDetails):
            css_requirements = ['foo.css', 'bar.css']
            js_requirements = ['foo.js', 'bar.js']

        class NoDuplicatesTab1(ResourceTab):
            css_requirements = ['foo1.css', 'bar1.css']
            js_requirements = ['foo1.js', 'bar1.js']

        class DuplicateJsTab(ResourceTab):
            css_requirements = ['foo2.css', 'bar2.css']
            js_requirements = ['foo2.js', 'bar2.js', 'foo1.js']

        instance = NoDuplicatesTrd()
        tabs = ({'slug': 'a-tab', 'title': 'A Tab', 'view': NoDuplicatesTab1},
                {'slug': 'another-tab', 'title': 'Another Tab', 'view': DuplicateJsTab})

        ret = instance.build_static_requirements(tabs)

        self.assertEqual(2, len(ret))
        self.assertListEqual(['foo.css', 'bar.css', 'foo1.css', 'bar1.css', 'foo2.css', 'bar2.css'], ret[0])
        self.assertListEqual(['foo.js', 'bar.js', 'foo1.js', 'bar1.js', 'foo2.js', 'bar2.js'], ret[1])

    def test_get_context_default(self):
        """Test default implementation of get_context."""
        instance = TabbedResourceDetails()
        tab_slug = 'a-tab'
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})
        in_context = {'foo': 'bar'}

        ret = instance.get_context(request, copy.deepcopy(in_context))

        self.assertDictEqual(in_context, ret)

    def test_get_tabs_self_tabs_not_none(self):
        """Test case when self.tabs is defined."""

        expected_tabs = ({'slug': 'a-tab', 'title': 'A Tab', 'view': TestTab1},
                         {'slug': 'another-tab', 'title': 'Another Tab', 'view': TestTab2})

        tab_slug = 'a-tab'
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})

        class TabsPropertyTrd(TabbedResourceDetails):
            tabs = copy.deepcopy(expected_tabs)

        instance = TabsPropertyTrd()

        ret = instance.get_tabs(request, self.resource, tab_slug)

        self.assertTupleEqual(expected_tabs, ret)

    def test_get_tabs_self_tabs_none(self):
        """Test case when self.tabs is not defined."""
        expected_tabs = ({'slug': 'tab1', 'title': 'Tab 1', 'view': ResourceTab},
                         {'slug': 'tab2', 'title': 'Tab 2', 'view': ResourceTab})

        tab_slug = 'a-tab'
        request = self.get_request_with_user(f'/foo/{self.resource.id}/bar/{tab_slug}/', 'get',
                                             {'tab_action': 'default'})

        instance = TabbedResourceDetails()

        ret = instance.get_tabs(request, self.resource, tab_slug)

        self.assertTupleEqual(expected_tabs, ret)
