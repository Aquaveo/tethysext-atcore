from unittest import mock
from .common import RWS_DEFAULT_OPTIONS
from tethysext.atcore.models.resource_workflow_steps import SpatialAttributesRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests,\
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialAttributesRWSTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        m = mock.MagicMock()
        m.__reduce__ = lambda self: (mock.MagicMock, ())
        self.instance = SpatialAttributesRWS(geoserver_name='', map_manager=m, spatial_manager=m)

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(SpatialAttributesRWS).get(self.instance.id)
        self.assertEqual(self.instance, ret)

    def test_default_options(self):
        baseline = {
            'geometry_source': None,
            'attributes': {},
            'geocode_enabled': False,
            **RWS_DEFAULT_OPTIONS
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_init_parameters(self):
        baseline = {
            'attributed_geometry': {
                'help': 'Valid GeoJSON representing geometry input by user.',
                'value': None,
                'required': False
            },
        }
        self.assertDictEqual(baseline, self.instance.init_parameters())

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_attributes_rws.SpatialResourceWorkflowStep.validate')  # noqa: E501
    def test_validate(self, mock_super_validate):
        self.instance.validate()
        mock_super_validate.assert_called()
