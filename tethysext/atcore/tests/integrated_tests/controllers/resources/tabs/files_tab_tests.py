"""
********************************************************************************
* Name: files_tab_tests.py
* Author: gagelarsen
* Created On: December 07, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
from unittest import mock
import uuid

from django.http import HttpResponse, Http404
from django.test import RequestFactory

from tethysext.atcore.models.file_database import FileCollection, FileDatabase
from tethysext.atcore.services.file_database import FileCollectionClient, FileDatabaseClient
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


class FilesTabTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request_factory = RequestFactory()

        self.resource = Resource(
            name="Test Resource"
        )

        self.test_files_base = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..',
                         '..', 'files', 'files_tab_tests')
        )

        self.test_path = os.path.join(self.test_files_base, 'test_get_context_default')
        self.database_client, self.collection = self.get_database_and_collection(
            uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}'), self.test_path,
            uuid.UUID('{d6fa7e10-d8aa-4b3d-b08a-62384d3daca2}')
        )

        self.file_collection_client = FileCollectionClient(self.session, self.database_client, self.collection.id)

        self.session.add(self.resource)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def get_database_and_collection(self, database_id, root_directory, collection_id,
                                    database_meta=None, collection_meta=None):
        """
        A helper function to generate a FileDatabase and a FileCollection in the database.

        Args:
            database_id (uuid.UUID): a UUID to assign the id for the FileDatabase object
            root_directory (str): root directory for a FileDatabase
            collection_id (uuid.UUID): a UUID to assign the id for the FileCollection object
            database_meta (dict): A dictionary of meta for the FileDatabase object
            collection_meta (dict): A dictionary of meta for the FileCollection object
        """
        database_meta = database_meta or {}
        collection_meta = collection_meta or {}
        database_instance = FileDatabase(
            id=database_id,  # We need to set the id here for the test path.
            meta=database_meta,
        )

        self.session.add(database_instance)
        self.session.commit()

        collection_instance = FileCollection(
            id=collection_id,
            file_database_id=database_id,
            meta=collection_meta,
        )

        self.session.add(collection_instance)
        self.session.commit()

        database_client = FileDatabaseClient(
            session=self.session,
            root_directory=root_directory,
            file_database_id=database_instance.id
        )

        return database_client, collection_instance

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
        ret = instance.get_file_collections(request, self.resource, self.session)
        self.assertListEqual([], ret)

    def test_get_context_default(self):
        """Test get_context()"""
        with mock.patch.object(ResourceFilesTab, 'get_file_collections') as mock_get_file_collection:

            instance = ResourceFilesTab()
            request = self.request_factory.get('/foo/12345/bar/summary/')
            request.user = self.get_user()

            mock_get_file_collection.return_value = [self.file_collection_client]
            context = instance.get_context(request, self.session, self.resource, {})

            self.assertIn('collections', context)
            self.assertEqual(len(context['collections']), 1)

    def test_download_file(self):
        """Test default implementation of get_summary_tab_info."""
        with mock.patch.object(ResourceFilesTab, 'get_file_collections') as mock_get_file_collection:
            instance = ResourceFilesTab()

            mock_get_file_collection.return_value = [self.file_collection_client]

            request = self.request_factory.get('/foo/12345/bar/files/?tab_action=download_file'
                                               '&file-path=d6fa7e10-d8aa-4b3d-b08a-62384d3daca2/dir1/file1.txt'
                                               '&collection-id=d6fa7e10-d8aa-4b3d-b08a-62384d3daca2')

            ret = instance.download_file(request, self.resource, self.session)
            self.assertTrue(isinstance(ret, HttpResponse))
            self.assertEqual(ret.content, b'Text for test to check.')
            self.assertEqual(ret['Content-Disposition'], 'filename=file1.txt')

    def test_download_file_fail(self):
        """Test default implementation of get_summary_tab_info."""
        with mock.patch.object(ResourceFilesTab, 'get_file_collections') as mock_get_file_collection:
            instance = ResourceFilesTab()

            mock_get_file_collection.return_value = [self.file_collection_client]

            request = self.request_factory.get('/foo/12345/bar/files/?tab_action=download_file'
                                               '&file-path=d6fa7e10-d8aa-4b3d-b08a-62384d3daca2/dir1/file9.txt'
                                               '&collection-id=d6fa7e10-d8aa-4b3d-b08a-62384d3daca2')

            with self.assertRaises(Http404) as exc:
                _ = instance.download_file(request, self.resource, self.session)

            self.assertTrue('Unable to download file.' in str(exc.exception))

    def test_path_hierarchy(self):
        test_path = os.path.join(self.test_files_base, 'test_path_hierarchy')
        instance = ResourceFilesTab()
        hierarchy = instance._path_hierarchy(os.path.join(test_path, 'dir1'))
        self.assertEqual(hierarchy['name'], 'dir1')
        self.assertEqual(len(hierarchy['children']), 3)
        expected_names = ['file4.txt', 'dir2', 'file3.txt']
        for child in hierarchy['children']:
            self.assertTrue(child['name'] in expected_names)
            expected_names.remove(child['name'])

    def test_path_hierarchy_ignore_pattern(self):
        test_path = os.path.join(self.test_files_base, 'test_path_hierarchy_ignore_pattern')
        instance = ResourceFilesTab()
        instance.file_hide_patterns = [r'.*\.json']
        hierarchy = instance._path_hierarchy(os.path.join(test_path, 'dir1'))
        self.assertEqual(hierarchy['name'], 'dir1')
        self.assertEqual(len(hierarchy['children']), 2)
        expected_names = ['file4.txt', 'dir2']
        for child in hierarchy['children']:
            self.assertTrue(child['name'] in expected_names)
            expected_names.remove(child['name'])

    def test_path_hierarchy_display_name(self):
        test_path = os.path.join(self.test_files_base, 'test_path_hierarchy_display_name')
        instance = ResourceFilesTab()
        hierarchy = instance._path_hierarchy(os.path.join(test_path, 'dir1'))
        self.assertEqual(hierarchy['name'], 'Good Name')

    def test_path_hierarchy_display_name_error(self):
        test_path = os.path.join(self.test_files_base, 'test_path_hierarchy_display_name_error')
        instance = ResourceFilesTab()
        hierarchy = instance._path_hierarchy(os.path.join(test_path, 'dir1'))
        self.assertEqual(hierarchy['name'], 'dir1')
