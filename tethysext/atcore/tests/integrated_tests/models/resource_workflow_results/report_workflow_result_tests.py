from unittest import mock
from tethysext.atcore.models.resource_workflow_results import ReportWorkflowResult
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ReportWorkflowResultTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = ReportWorkflowResult(
            name='test',
            geoserver_name='geoserver_name',
            map_manager='map_manager',
            spatial_manager='spatial_manager'
        )

    def bind_instance_to_session(self):
        self.session.add(self.instance)
        self.session.commit()

    def test_default_options(self):
        self.assertDictEqual({}, self.instance.default_options)
