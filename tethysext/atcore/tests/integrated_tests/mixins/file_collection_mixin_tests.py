import datetime
import os
import shutil
import uuid

from sqlalchemy.orm import relationship, backref

from tethysext.atcore.mixins.file_collection_mixin import FileCollectionMixin
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.models.file_database import FileCollection, FileDatabase, resource_file_collection_association
from tethysext.atcore.services.file_database import FileCollectionClient, FileDatabaseClient
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


class TestResourceWithFiles(Resource, FileCollectionMixin):
    TYPE = 'test_resource_with_files'

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }

    file_collections = relationship(
        FileCollection,
        secondary=resource_file_collection_association,
        backref=backref('test_file_resource', uselist=False)
    )


def setUpModule():
    global test_files_root, test_files_temp, test_files_base
    setup_module_for_sqlalchemy_tests()
    test_files_root = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '../models', '..', '..', 'files')
    )
    test_files_base = os.path.join(test_files_root, 'file_collection_mixin_tests')
    test_files_temp = os.path.join(test_files_root, 'temp', 'file_collection_mixin_tests')


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()
    if os.path.exists(test_files_temp):
        shutil.rmtree(test_files_temp)


class FileCollectionMixinTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.name = "test_resource"
        self.description = "Bad Description"
        self.status = "Processing"
        self.creation_date = datetime.datetime.utcnow()

        # Test specific directories
        self.test_dir_name = self._testMethodName
        self.base_files_root_dir = os.path.join(test_files_base, self.test_dir_name)
        self.root_dir = os.path.join(test_files_temp, self.test_dir_name)

        if os.path.exists(self.root_dir):
            shutil.rmtree(self.root_dir)

        if os.path.exists(self.base_files_root_dir):
            shutil.copytree(
                self.base_files_root_dir,
                self.root_dir,
                ignore=shutil.ignore_patterns('.keep')
            )

        # ID's to use for testing. Directories will need to be named this.
        self.general_database_id = uuid.UUID('{da37af40-8474-4025-9fe4-c689c93299c5}')

    def get_database_client(self, database_id, root_directory, database_meta=None):
        """
        A helper function to generate a FileDatabase and FileDatabaseClient.

        Args:
            database_id (uuid.UUID): a UUID to assign the id for the FileDatabase object
            root_directory (str): root directory for a FileDatabaseClient
            database_meta (dict): A dictionary of meta for the FileDatabase object
        """
        if database_meta is None:
            database_meta = {}

        database_instance = FileDatabase(
            id=database_id,  # We need to set the id here for the test path.
            meta=database_meta,
        )

        self.session.add(database_instance)
        self.session.commit()

        database_client = FileDatabaseClient(
            session=self.session,
            root_directory=root_directory,
            file_database_id=database_instance.id
        )

        return database_client

    def test_new(self):
        """Test creating a new resource."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
        ]
        resource = TestResourceWithFiles.new(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date,
            file_database_client=database_client,
            files=files
        )
        collection_count = self.session.query(FileCollection).count()
        resource_count = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count, 1)
        self.assertEqual(resource_count, 1)
        self.assertTrue(len(resource.file_collections) == 1)
        self.assertEqual(resource.name, self.name)
        self.assertEqual(resource.description, self.description)
        self.assertEqual(resource.status, self.status)
        self.assertEqual(resource.date_created, self.creation_date)

        file_collection = resource.file_collections[0]
        collection_client = FileCollectionClient(self.session, database_client, file_collection.id)
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'file1.txt')))

    def test_new_multiple_files(self):
        """Test creating a resource with multiple files."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files)
        collection_count = self.session.query(FileCollection).count()
        resource_count = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count, 1)
        self.assertEqual(resource_count, 1)
        self.assertTrue(len(resource.file_collections) == 1)

        file_collection = resource.file_collections[0]
        collection_client = FileCollectionClient(self.session, database_client, file_collection.id)
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'file2.txt')))

    def test_new_multiple_collections(self):
        """Test creating a resource with items specified to be in separate collections."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files, separate_collections=True)
        collection_count = self.session.query(FileCollection).count()
        resource_count = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count, 2)
        self.assertEqual(resource_count, 1)
        self.assertTrue(len(resource.file_collections) == 2)

    def test_new_directory(self):
        """Test creating a resource with items being a directory."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'dir1'),
        ]
        resource = TestResourceWithFiles.new(database_client, files)
        collection_count = self.session.query(FileCollection).count()
        resource_count = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count, 1)
        self.assertEqual(resource_count, 1)
        self.assertTrue(len(resource.file_collections) == 1)

        file_collection = resource.file_collections[0]
        collection_client = FileCollectionClient(self.session, database_client, file_collection.id)
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'dir1', 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(collection_client.path, 'dir1', 'file2.txt')))

    def test_export(self):
        """Test exporting a resource resource with single collection."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files)
        file_collection = resource.file_collections[0]
        collection_client = FileCollectionClient(self.session, database_client, file_collection.id)

        export_dir = os.path.join(self.root_dir, 'export_files')
        resource.export(database_client, export_dir)
        self.assertTrue(os.path.exists(os.path.join(export_dir, str(file_collection.id))))
        for root, _dirs, files in collection_client.walk():
            for file in files:
                self.assertTrue(os.path.exists(
                    os.path.join(export_dir, str(collection_client.instance.id), root, file))
                )

    def test_export_multiple(self):
        """Test exporting a resource with multiple collections."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files, separate_collections=True)
        file_collection_1 = resource.file_collections[0]
        file_collection_2 = resource.file_collections[1]
        collection_client_1 = FileCollectionClient(self.session, database_client, file_collection_1.id)
        collection_client_2 = FileCollectionClient(self.session, database_client, file_collection_2.id)

        export_dir = os.path.join(self.root_dir, 'export_files')
        resource.export(database_client, export_dir)
        self.assertTrue(os.path.exists(os.path.join(export_dir, str(file_collection_1.id))))
        self.assertTrue(os.path.exists(os.path.join(export_dir, str(file_collection_2.id))))
        for root, _dirs, files in collection_client_1.walk():
            for file in files:
                self.assertTrue(os.path.exists(
                    os.path.join(export_dir, str(collection_client_1.instance.id), root, file))
                )
        for root, _dirs, files in collection_client_2.walk():
            for file in files:
                self.assertTrue(os.path.exists(
                    os.path.join(export_dir, str(collection_client_2.instance.id), root, file))
                )

    def test_duplicate(self):
        """Test duplicating a resource with single collection."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files)
        collection_count_before = self.session.query(FileCollection).count()
        resource_count_before = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count_before, 1)
        self.assertEqual(resource_count_before, 1)
        _ = resource.duplicate(database_client)
        collection_count_after = self.session.query(FileCollection).count()
        resource_count_after = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count_after, 2)
        self.assertEqual(resource_count_after, 2)

    def test_duplicate_multiple_collections(self):
        """Test duplicating a resource with multiple collections."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files, separate_collections=True)
        collection_count_before = self.session.query(FileCollection).count()
        resource_count_before = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count_before, 2)
        self.assertEqual(resource_count_before, 1)
        _ = resource.duplicate(database_client)
        collection_count_after = self.session.query(FileCollection).count()
        resource_count_after = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count_after, 4)
        self.assertEqual(resource_count_after, 2)

    def test_delete_collections(self):
        """Test deleting a resource with single collection."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files)
        collection_count_before = self.session.query(FileCollection).count()
        resource_count_before = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count_before, 1)
        self.assertEqual(resource_count_before, 1)
        resource.delete_collections(self.root_dir)
        collection_count_after = self.session.query(FileCollection).count()
        self.assertEqual(collection_count_after, 0)

    def test_delete_collections_multiple_collections(self):
        """Test deleting a resource with multiple collections."""
        database_client = self.get_database_client(self.general_database_id, self.root_dir)
        files = [
            os.path.join(self.root_dir, 'files', 'file1.txt'),
            os.path.join(self.root_dir, 'files', 'file2.txt'),
        ]
        resource = TestResourceWithFiles.new(database_client, files, separate_collections=True)
        collection_count_before = self.session.query(FileCollection).count()
        resource_count_before = self.session.query(TestResourceWithFiles).count()
        self.assertEqual(collection_count_before, 2)
        self.assertEqual(resource_count_before, 1)
        resource.delete_collections(self.root_dir)
        collection_count_after = self.session.query(FileCollection).count()
        self.assertEqual(collection_count_after, 0)
