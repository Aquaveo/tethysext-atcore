import datetime
import mock
import os
from pathlib import Path
import shutil

from sqlalchemy.orm import backref, relationship

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.models.file_database import FileCollection, resource_file_collection_association
from tethysext.atcore.services.file_database import FileDatabaseClient
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase, setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests

from tethysext.atcore.mixins.file_collection_controller_mixin import FileCollectionsControllerMixin


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FileCollectionResource(Resource):
    TYPE = 'test_file_collection_resource'
    DISPLAY_TYPE_SINGULAR = 'File Collection Resource'
    DISPLAY_TYPE_PLURAL = 'File Collection Resource'

    file_collections = relationship(FileCollection, secondary=resource_file_collection_association,
                                    backref=backref('fcr', uselist=False))

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }


class FileCollectionsControllerMixinTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.path = os.path.join(Path(__file__).parents[2], 'files', 'file_collection_controller_mixin_tests')
        # Create a copy and test files there
        self.test_folder_path = os.path.join(self.path, 'result')
        if os.path.isdir(self.test_folder_path):
            shutil.rmtree(self.test_folder_path)
        shutil.copytree(self.path, self.test_folder_path)

        self.mixin = FileCollectionsControllerMixin()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.test_folder_path)

    @mock.patch('tethysext.atcore.mixins.file_collection_controller_mixin.FileDatabaseClient.delete_collection')
    def test_delete_file_collections(self, mock_delete):
        mock_log = mock.MagicMock()

        resource = FileCollectionResource(
            name='Foo Resource',
            description='Foo Bar',
            created_by='foo',
            date_created=datetime.datetime.utcnow(),
        )

        resource.set_attribute('files', [os.path.join(self.test_folder_path, 'dataset_data.zip')])
        resource.set_attribute('srid', 4326)

        file_database = FileDatabaseClient.new(self.session, root_directory=self.test_folder_path)
        mock_app = mock.MagicMock()
        mock_app.get_custom_setting.return_value = str(file_database.instance.id)
        self.mixin.get_app = mock.MagicMock(return_value=mock_app)

        fcc = file_database.new_collection()
        resource.file_collections.append(fcc.instance)
        file_collection_id = fcc.instance.id

        self.session.add(resource)
        self.session.commit()

        self.mixin.delete_file_collections(
            session=self.session,
            resource=resource,
            log=mock_log
        )

        mock_delete.assert_called_with(file_collection_id)

    @mock.patch('tethysext.atcore.mixins.file_collection_controller_mixin.FileDatabaseClient')
    def test_delete_file_collection_exception(self, mock_fdc):
        mock_log = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_resource = mock.MagicMock(id='0123456789', file_collections=[mock.MagicMock()])
        mock_fdc().delete_collection.side_effect = Exception('Test Exception')

        self.mixin.delete_file_collections(
            session=mock_session,
            resource=mock_resource,
            log=mock_log
        )

        mock_log.exception.assert_called_with(
            'The file collection(s) associated with resource 0123456789 could not be deleted.'
        )

    @mock.patch('tethysext.atcore.mixins.file_collection_controller_mixin.os.path.getsize')
    @mock.patch('tethysext.atcore.mixins.file_collection_controller_mixin.FileDatabaseClient')
    def test_get_file_collections_details(self, mock_fdbc, mock_getsize):
        mock_session = mock.MagicMock()
        mock_file_collection = mock.MagicMock(id='test_id', meta={'test_key': 'test_value'})
        mock_resource = mock.MagicMock(file_collections=[mock_file_collection])
        mock_fcc_walk = mock.MagicMock(return_value=[('test_root', ['test_dirs'], ['test_Files'])])
        mock_fdbc().get_collection.return_value = mock.MagicMock(path='test_path', walk=mock_fcc_walk)
        mock_getsize.return_value = 2e12
        self.mixin.get_app = mock.MagicMock()

        ret = self.mixin.get_file_collections_details(mock_session, mock_resource)

        expected_result = [
            ('File Collection Details', {
                'ID': 'test_id',
                'File count': 1,
                'Total Size': '1.82 TB',  # f'{2e12/(1024.0**4):.2f} TB'
                'test_key': 'test_value'
            })
        ]

        self.assertEqual(ret, expected_result)
