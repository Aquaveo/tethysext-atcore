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

from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resources import ResourceTab, ResourceSummaryTab


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SummaryTabWithPreviewImage(ResourceSummaryTab):
    preview_image_title = 'Foo'
    has_preview_image = True

    def get_preview_image_url(self, request, resource, *args, **kwargs):
        return 'https://i.redd.it/j7ne5n5qxsy51.png'


class SummaryTabWithCustomInfo(ResourceSummaryTab):

    def get_summary_tab_info(self, request, resource, *args, **kwargs):
        return [
            [
                ('Foo Title', {'Count': 1}),
                ('Bar Title', {'Result': 10.0, 'Name': 'Foo'}),
            ], [
                ('Baz Title', {'Active': True}),
            ],
        ]


class SummaryTabWithBoth(SummaryTabWithCustomInfo, SummaryTabWithPreviewImage):
    pass


class ResourceSummaryTabTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request_factory = RequestFactory()

        self.resource = Resource(
            name="Test Resource"
        )

        self.resource.set_attribute('num_hours', 1986)
        self.resource.set_attribute('favorite_quote', 'This is the way')

        self.session.add(self.resource)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def get_user(self, is_staff=False, return_app_user=False):
        """Make a Django User and/or associated AppUser instance."""
        django_user = UserFactory()
        django_user.is_staff = is_staff
        django_user.is_superuser = is_staff
        django_user.save()

        app_user = AppUser(
            username=django_user.username,
            role=Roles.DEVELOPER if is_staff else Roles.ORG_USER,
            is_active=True,
        )
        self.session.add(app_user)
        self.session.commit()

        return app_user if return_app_user else django_user

    def verify_general_summary_tab_info(self, context):
        """Asserts to verify the general summary tab info that is included in every summary tab view."""
        general_table = context['columns'][0][0]
        general_table_title = general_table[0]
        general_table_entries = general_table[1]

        self.assertEqual('Description', general_table_title)
        self.assertDictEqual(
            {'Name': self.resource.name,
             'Description': self.resource.description,
             'Created By': self.resource.created_by,
             'Date Created': self.resource.date_created},
            general_table_entries
        )

    def verify_custom_summary_tab_info(self, context):
        """Asserts to verify the custom summary tab info added by SummaryTabWithCustomInfo."""
        foo_table = context['columns'][0][1]
        bar_table = context['columns'][0][2]
        baz_table = context['columns'][1][0]

        self.assertEqual('Foo Title', foo_table[0])
        self.assertDictEqual({'Count': 1}, foo_table[1])
        self.assertEqual('Bar Title', bar_table[0])
        self.assertDictEqual({'Result': 10.0, 'Name': 'Foo'}, bar_table[1])
        self.assertEqual('Baz Title', baz_table[0])
        self.assertDictEqual({'Active': True}, baz_table[1])

    def verify_debug_summary_tab_info(self, context, locked=False, locked_by='N/A'):
        """Asserts to verify the debug summary tab info added by for staff users."""
        debug_table = context['columns'][-1][-1]  # last table in last column
        debug_table_title = debug_table[0]
        debug_table_entries = debug_table[1]

        self.assertEqual('Debug Info', debug_table_title)

        self.assertDictEqual(
            {'Favorite Quote': 'This is the way',
             'Locked': locked,
             'Locked By': locked_by,
             'Num Hours': 1986},
            debug_table_entries
        )

    def test_properties_default(self):
        """Verify the default values for the properties of the view."""
        self.assertEqual('atcore/resources/tabs/summary_tab.html', ResourceSummaryTab.template_name)
        self.assertEqual('summary_tab_loaded', ResourceSummaryTab.post_load_callback)
        self.assertEqual('Preview', ResourceSummaryTab.preview_image_title)
        self.assertFalse(ResourceSummaryTab.has_preview_image)
        self.assertIn('atcore/resources/summary_tab.js', ResourceSummaryTab.js_requirements)

        # Ensure the default js_requirements for ResourceTabs are also included
        for js_requirement in ResourceTab.js_requirements:
            self.assertIn(js_requirement, ResourceSummaryTab.js_requirements)

    def test_get_preview_image_url_default(self):
        """Test default implementation of get_preview_image_url."""
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        ret = instance.get_preview_image_url(request, self.resource)
        self.assertIsNone(ret)

    def test_get_summary_tab_info_default(self):
        """Test default implementation of get_summary_tab_info."""
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        ret = instance.get_summary_tab_info(request, self.resource)
        self.assertListEqual([], ret)

    @mock.patch('tethysext.atcore.controllers.resources.tabs.summary_tab.render')
    def test_load_summary_tab_preview_image_no_preview_image(self, mock_render):
        """Test load_summary_tab_preview_image with default implementation of get_preview_image_url (None)."""
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')

        ret = instance.load_summary_tab_preview_image(request, self.resource)

        expected_context = {
            'preview_title': 'Preview',
            'preview_map_url': None
        }
        mock_render.assert_called_with(
            request, 'atcore/resources/tabs/summary_preview_image.html', expected_context
        )
        self.assertEqual(mock_render(), ret)

    @mock.patch('tethysext.atcore.controllers.resources.tabs.summary_tab.render')
    def test_load_summary_tab_preview_image_with_preview_image(self, mock_render):
        """Test load_summary_tab_preview_image with image url defined by get_preview_image_url."""
        request = self.request_factory.get('/foo/12345/bar/summary/')
        instance = SummaryTabWithPreviewImage()

        ret = instance.load_summary_tab_preview_image(request, self.resource)

        expected_context = {
            'preview_title': 'Foo',
            'preview_map_url': 'https://i.redd.it/j7ne5n5qxsy51.png'
        }
        mock_render.assert_called_with(
            request, 'atcore/resources/tabs/summary_preview_image.html', expected_context
        )
        self.assertEqual(mock_render(), ret)

    def test_default_get_context(self):
        """Test get_context() with default implementation: no preview image, no summary tab info, user not staff."""
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertNotIn('has_preview_image', context)
        self.assertNotIn('preview_image_title', context)

        self.assertIn('columns', context)
        self.assertEqual(1, len(context['columns']))  # 1 column
        self.assertEqual(1, len(context['columns'][0]))  # 1 table

        self.verify_general_summary_tab_info(context)

    def test_get_context_preview_image(self):
        """Test get_context() with only preview image defined."""
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()
        instance = SummaryTabWithPreviewImage()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('has_preview_image', context)
        self.assertTrue(context['has_preview_image'])
        self.assertIn('preview_image_title', context)
        self.assertEqual('Foo', context['preview_image_title'])

        self.assertIn('columns', context)
        self.assertEqual(1, len(context['columns']))  # 1 column
        self.assertEqual(1, len(context['columns'][0]))  # 1 table

        self.verify_general_summary_tab_info(context)

    def test_get_context_summary_tab_info(self):
        """Test get_context() with only summary tab info defined."""
        instance = SummaryTabWithCustomInfo()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertNotIn('has_preview_image', context)
        self.assertNotIn('preview_image_title', context)

        self.assertIn('columns', context)
        self.assertEqual(2, len(context['columns']))  # 2 columns
        self.assertEqual(3, len(context['columns'][0]))  # 3 tables in column 1
        self.assertEqual(1, len(context['columns'][1]))  # 1 table in column 2

        self.verify_general_summary_tab_info(context)
        self.verify_custom_summary_tab_info(context)

    def test_get_context_preview_image_and_summary_tab_info(self):
        """Test get_context() with preview image and summary tab info defined."""
        """Test get_context() with only summary tab info defined."""
        instance = SummaryTabWithBoth()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('has_preview_image', context)
        self.assertTrue(context['has_preview_image'])
        self.assertIn('preview_image_title', context)
        self.assertEqual('Foo', context['preview_image_title'])

        self.assertIn('columns', context)
        self.assertEqual(2, len(context['columns']))  # 2 columns
        self.assertEqual(3, len(context['columns'][0]))  # 3 tables in column 1
        self.assertEqual(1, len(context['columns'][1]))  # 1 table in column 2

        self.verify_general_summary_tab_info(context)
        self.verify_custom_summary_tab_info(context)

    def test_get_context_staff_user(self):
        """Test that debug information is generated for staff users."""
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user(is_staff=True)

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('columns', context)
        self.assertEqual(1, len(context['columns']))  # 1 column
        self.assertEqual(2, len(context['columns'][0]))  # 2 tables in column 1

        self.verify_general_summary_tab_info(context)
        self.verify_debug_summary_tab_info(context)

    def test_get_context_preview_image_and_summary_tab_info_staff_user(self):
        """Test that the debug information is appended to the end of the last column."""
        instance = SummaryTabWithBoth()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user(is_staff=True)

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('columns', context)
        self.assertEqual(2, len(context['columns']))  # 2 columns
        self.assertEqual(3, len(context['columns'][0]))  # 3 tables in column 1
        self.assertEqual(2, len(context['columns'][1]))  # 2 table in column 2

        self.verify_general_summary_tab_info(context)
        self.verify_custom_summary_tab_info(context)
        self.verify_debug_summary_tab_info(context)

    def test_get_context_staff_user_resource_locked_for_specific_user(self):
        """
        Test that username with user lock is displayed in debug information
        when resource is locked by a specific user.
        """
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        user = self.get_user(is_staff=True)
        request.user = user
        self.resource.acquire_user_lock(request)

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('columns', context)
        self.assertEqual(1, len(context['columns']))  # 1 column
        self.assertEqual(2, len(context['columns'][0]))  # 2 tables in column 1

        self.verify_general_summary_tab_info(context)
        self.verify_debug_summary_tab_info(context, locked=True, locked_by=user.username)

    def test_get_context_staff_user_resource_locked_for_all_users(self):
        """Test that "All Users" is displayed in debug information when resource is locked for all users."""
        instance = ResourceSummaryTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        user = self.get_user(is_staff=True)
        request.user = user
        self.resource.acquire_user_lock()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('columns', context)
        self.assertEqual(1, len(context['columns']))  # 1 column
        self.assertEqual(2, len(context['columns'][0]))  # 2 tables in column 1

        self.verify_general_summary_tab_info(context)
        self.verify_debug_summary_tab_info(context, locked=True, locked_by='All Users')
