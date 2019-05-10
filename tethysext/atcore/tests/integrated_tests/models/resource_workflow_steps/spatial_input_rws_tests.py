import mock
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests,\
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialInputRWSTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        m = mock.MagicMock()
        m.__reduce__ = lambda self: (mock.MagicMock, ())
        self.instance = SpatialInputRWS(geoserver_name='', map_manager=m, spatial_manager=m)

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(SpatialInputRWS).get(self.instance.id)
        self.assertEqual(self.instance, ret)

    def test_default_options(self):
        baseline = {
            'shapes': ['points', 'lines', 'polygons', 'extents'],
            'singular_name': 'Feature',
            'plural_name': 'Features',
            'allow_shapefile': True,
            'allow_drawing': True,
            'snapping_enabled': True,
            'snapping_layer': {},
            'snapping_options': {}
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_init_parameters(self):
        baseline = {
            'geometry': {
                'help': 'Valid GeoJSON representing geometry input by user.',
                'value': None,
                'required': False
            },
        }
        self.assertDictEqual(baseline, self.instance.init_parameters())

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_input_rws.SpatialResourceWorkflowStep.validate')  # noqa: E501
    def test_to_geojson_string(self, mock_validate):
        self.instance.validate()
        mock_validate.assert_called()
