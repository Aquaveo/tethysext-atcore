from unittest import mock
from tethysext.atcore.models.resource_workflow_steps import SpatialResourceWorkflowStep
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialResourceWorkflowStepTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        # Custom setup here
        m = mock.MagicMock()
        m.__reduce__ = lambda self: (mock.MagicMock, ())
        self.instance = SpatialResourceWorkflowStep(geoserver_name='', map_manager=m, spatial_manager=m)

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(SpatialResourceWorkflowStep).get(self.instance.id)
        self.assertEqual(self.instance, ret)

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_rws.SpatialResourceWorkflowStep.get_parameter')
    def test_to_geojson(self, mock_get_param):
        baseline = {"foo": "bar"}
        mock_get_param.return_value = baseline
        ret = self.instance.to_geojson(as_str=False)
        self.assertEqual(baseline, ret)

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_rws.SpatialResourceWorkflowStep.get_parameter')
    def test_to_geojson_string(self, mock_get_param):
        baseline = {"foo": "bar"}
        mock_get_param.return_value = baseline
        ret = self.instance.to_geojson(as_str=True)
        self.assertEqual('{"foo": "bar"}', ret)
