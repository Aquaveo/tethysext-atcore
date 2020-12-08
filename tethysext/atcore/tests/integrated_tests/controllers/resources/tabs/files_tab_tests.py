"""
********************************************************************************
* Name: files_tab_tests.py
* Author: gagelarsen
* Created On: December 07, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os

from django.test import RequestFactory

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.controllers.resources import ResourceTab, ResourceFilesTab


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FilesTabWithDatabase(ResourceFilesTab):

    def get_file_collections(self, request, resource, *args, **kwargs):
        return []


class ResourceFilesTabTests(SqlAlchemyTestCase):

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
        """Verify the default values for the properties of the view."""
        self.assertEqual('atcore/resources/tabs/files_tab.html', ResourceFilesTab.template_name)
        self.assertEqual('files_tab_loaded', ResourceFilesTab.post_load_callback)
        self.assertIn('atcore/resources/files_tab.js', ResourceFilesTab.js_requirements)
        self.assertIn('atcore/resources/files_tab.css', ResourceFilesTab.css_requirements)

        # Ensure the default js_requirements for ResourceTabs are also included
        for js_requirement in ResourceTab.js_requirements:
            self.assertIn(js_requirement, ResourceFilesTab.js_requirements)

        for css_requirement in ResourceTab.css_requirements:
            self.assertIn(css_requirement, ResourceFilesTab.css_requirements)

    def test_get_files_tab(self):
        """Test default implementation of get_summary_tab_info."""
        instance = ResourceFilesTab()
        request = self.request_factory.get('/foo/12345/bar/files/')
        ret = instance.get_file_collections(request, self.resource)
        self.assertListEqual([], ret)

    def test_get_context_default(self):
        """Test get_context() with default implementation: no preview image, no summary tab info, user not staff."""
        instance = ResourceFilesTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('collections', context)

    def test_get_context_staff_user(self):
        """Test that debug information is generated for staff users."""
        instance = ResourceFilesTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        request.user = self.get_user(is_staff=True)

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('collections', context)

    def test_get_context_staff_user_resource_locked_for_specific_user(self):
        """
        Test that username with user lock is displayed in debug information
        when resource is locked by a specific user.
        """
        instance = ResourceFilesTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        user = self.get_user(is_staff=True)
        request.user = user
        self.resource.acquire_user_lock(request)

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('collections', context)

    def test_get_context_staff_user_resource_locked_for_all_users(self):
        """Test that "All Users" is displayed in debug information when resource is locked for all users."""
        instance = ResourceFilesTab()
        request = self.request_factory.get('/foo/12345/bar/summary/')
        user = self.get_user(is_staff=True)
        request.user = user
        self.resource.acquire_user_lock()

        context = instance.get_context(request, self.session, self.resource, {})

        self.assertIn('collections', context)

    def test_path_hierarchy(self):
        test_files_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..',
                         'files', 'files_tab_tests', 'test_path_hierarchy')
        )
        instance = ResourceFilesTab()
        hierarchy = instance._path_hierarchy(test_files_path)
        expected_hierarchy = {
            'type': 'folder',
            'name': 'test_path_hierarchy',
            'path': '/test_path_hierarchy',
            'parent_path': '/',
            'parent_slug': None,
            'slug': '__test_path_hierarchy',
            'children': [{
                             'type': 'file',
                             'name': 'file2.txt',
                             'path': '/test_path_hierarchy/file2.txt',
                             'parent_path': '/test_path_hierarchy',
                             'parent_slug': '__test_path_hierarchy',
                             'slug': '__test_path_hierarchy_file2_txt',
                             'date_modified': 'Tue Dec  8 06:04:58 2020',
                             'size': '0 Bytes'}, {
                             'type': 'file',
                             'name': 'file1.txt',
                             'path': '/test_path_hierarchy/file1.txt',
                             'parent_path': '/test_path_hierarchy',
                             'parent_slug': '__test_path_hierarchy',
                             'slug': '__test_path_hierarchy_file1_txt',
                             'date_modified': 'Tue Dec  8 06:04:49 2020',
                             'size': '0 Bytes'}, {
                             'type': 'folder',
                             'name': 'dir1',
                             'path': '/test_path_hierarchy/dir1',
                             'parent_path': '/test_path_hierarchy',
                             'parent_slug': '__test_path_hierarchy',
                             'slug': '__test_path_hierarchy_dir1',
                             'children': [{
                                              'type': 'file',
                                              'name': 'file4.txt',
                                              'path': '/test_path_hierarchy/dir1/file4.txt',
                                              'parent_path': '/test_path_hierarchy/dir1',
                                              'parent_slug': '__test_path_hierarchy_dir1',
                                              'slug': '__test_path_hierarchy_dir1_file4_txt',
                                              'date_modified': 'Tue Dec  8 06:05:32 2020',
                                              'size': '0 Bytes'}, {
                                              'type': 'folder',
                                              'name': 'dir2',
                                              'path': '/test_path_hierarchy/dir1/dir2',
                                              'parent_path': '/test_path_hierarchy/dir1',
                                              'parent_slug': '__test_path_hierarchy_dir1',
                                              'slug': '__test_path_hierarchy_dir1_dir2',
                                              'children': [{
                                                               'type': 'file',
                                                               'name': 'file5.txt',
                                                               'path': '/test_path_hierarchy/dir1/dir2/file5.txt',
                                                               'parent_path': '/test_path_hierarchy/dir1/dir2',
                                                               'parent_slug': '__test_path_hierarchy_dir1_dir2',
                                                               'slug': '__test_path_hierarchy_dir1_dir2_file5_txt',
                                                               'date_modified': 'Tue Dec  8 06:05:47 2020',
                                                               'size': '0 Bytes'}],
                                              'date_modified': 'Tue Dec  8 06:05:47 2020'}, {
                                              'type': 'file',
                                              'name': 'file3.txt',
                                              'path': '/test_path_hierarchy/dir1/file3.txt',
                                              'parent_path': '/test_path_hierarchy/dir1',
                                              'parent_slug': '__test_path_hierarchy_dir1',
                                              'slug': '__test_path_hierarchy_dir1_file3_txt',
                                              'date_modified': 'Tue Dec  8 06:05:22 2020',
                                              'size': '0 Bytes'}],
                             'date_modified': 'Tue Dec  8 06:05:47 2020'}],
            'date_modified': 'Tue Dec  8 06:05:47 2020'
        }
        self.assertDictEqual(hierarchy, expected_hierarchy)
