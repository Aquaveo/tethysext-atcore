from unittest import mock
import param
from .common import RWS_DEFAULT_OPTIONS
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TestAttributes(param.Parameterized):
    location_name = param.String(allow_None=False)  #: Required
    location_type = param.String(allow_None=True)  #: Not Required
    cow_type = param.String(allow_None=False)  #: Required
    number_of_gates = param.Integer(allow_None=False)  #: Required
    number_of_cows = param.Integer(allow_None=False)  #: Required
    cow_flow = param.Number(allow_None=True, bounds=(0, 10000))  #: Not Required
    how_big = param.Magnitude(allow_None=True)  #: Not Required


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
            'snapping_options': {},
            'allow_image': False,
            'attributes': None,
            'geocode_enabled': False,
            'label_options': None,
            **RWS_DEFAULT_OPTIONS
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_init_parameters(self):
        baseline = {
            'geometry': {
                'help': 'Valid GeoJSON representing geometry input by user.',
                'value': None,
                'required': False
            },
            'imagery': {
                'help': 'GeoTiff background image input by user.',
                'value': None,
                'required': False,
            },
        }
        self.assertDictEqual(baseline, self.instance.init_parameters())

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_input_rws.SpatialResourceWorkflowStep.validate')  # noqa: E501
    def test_validate_no_attributes(self, mock_validate):
        ret = self.instance.validate()
        mock_validate.assert_called()
        self.assertTrue(ret)

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_input_rws.SpatialResourceWorkflowStep.validate')  # noqa: E501
    def test_validate_with_attributes(self, mock_validate):
        self.instance.validate_feature_attributes = mock.MagicMock()
        self.instance.options = {'attributes': mock.MagicMock()}

        mock_geometry = {
            'features': [{
                'properties': {'foo': 'bar'},
                'geometry': {}
            }]
        }

        self.instance.get_parameter = mock.MagicMock(return_value=mock_geometry)

        ret = self.instance.validate()

        mock_validate.assert_called()
        self.assertTrue(ret)
        self.instance.validate_feature_attributes.assert_called_with(mock_geometry['features'][0]['properties'])

    def test_validate_feature_attributes(self):
        self.instance.options = {'attributes': TestAttributes()}

        attributes = {
            'location_name': 'Provo',  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '355.8',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        ret = self.instance.validate_feature_attributes(attributes=attributes)

        self.assertTrue(ret)

    def test_validate_feature_attributes_no_attributes_definition(self):
        self.instance.options = {'attributes': None}

        attributes = {
            'location_name': 'Provo',  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '355.8',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        ret = self.instance.validate_feature_attributes(attributes=attributes)

        self.assertTrue(ret)

    def test_validate_feature_attributes_missing_not_required_attribute(self):
        self.instance.options = {'attributes': TestAttributes()}

        # Missing one not required attribute
        attributes = {
            'location_name': 'Provo',  # Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '355.8',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        ret = self.instance.validate_feature_attributes(attributes=attributes)

        self.assertTrue(ret)

    def test_validate_feature_attributes_missing_required_attribute(self):
        self.instance.options = {'attributes': TestAttributes()}

        # Missing one required attribute
        attributes = {
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '355.8',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        self.assertRaises(ValueError, self.instance.validate_feature_attributes, attributes=attributes)

    def test_validate_feature_attributes_none_for_required(self):
        self.instance.options = {'attributes': TestAttributes()}

        attributes = {
            'location_name': None,  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '355.8',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        self.assertRaises(ValueError, self.instance.validate_feature_attributes, attributes=attributes)

    def test_validate_feature_attributes_empty_string_for_required(self):
        self.instance.options = {'attributes': TestAttributes()}

        attributes = {
            'location_name': '',  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '355.8',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        self.assertRaises(ValueError, self.instance.validate_feature_attributes, attributes=attributes)

    def test_validate_feature_attributes_empty_string_for_not_required_number_field(self):
        self.instance.options = {'attributes': TestAttributes()}

        attributes = {
            'location_name': 'Provo',  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        self.assertRaises(ValueError, self.instance.validate_feature_attributes, attributes=attributes)

    def test_validate_feature_attributes_non_number_for_not_required_number_field(self):
        self.instance.options = {'attributes': TestAttributes()}

        attributes = {
            'location_name': 'Provo',  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': 'foo',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        self.assertRaises(ValueError, self.instance.validate_feature_attributes, attributes=attributes)

    def test_validate_feature_attributes_invalid_value(self):
        self.instance.options = {'attributes': TestAttributes()}

        attributes = {
            'location_name': 'Provo',  # Required
            'location_type': 'Municipality',  # Not Required
            'cow_type': 'Bovine',  # Required
            'number_of_gates': '10',  # Required
            'number_of_cows': '3',  # Required
            'cow_flow': '-10',  # Not Required, must be between 0 and 10000
            'how_big': '0.8'  # Not Required
        }

        self.assertRaises(ValueError, self.instance.validate_feature_attributes, attributes=attributes)

    def test__colloquialize_validation_error_attribute_name_not_in_message(self):
        message = 'An unexpected message without the attribute name was given.'
        attribute_name = 'location_name'
        attribute_title = 'Location Name'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual(f'{attribute_title}: {message}', ret)

    def test__colloquialize_validation_error_attribute_name_in_message(self):
        message = "Parameter integer must be at least 0."
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Integer must be at least 0.', ret)

    def test__colloquialize_validation_error_dq_attribute_name_in_message(self):
        message = 'Parameter "integer" must be at least 0.'
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Integer must be at least 0.', ret)

    def test__colloquialize_validation_error_sq_attribute_name_in_message(self):
        message = "Parameter 'integer' must be at least 0."
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Integer must be at least 0.', ret)

    def test__colloquialize_validation_error_attribute_name_in_message_twice(self):
        message = "Parameter integer must be an integer."
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Integer must be an integer.', ret)

    def test__colloquialize_validation_error_attribute_name_at_beginning_of_message(self):
        message = "integer must be at most 10."
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Integer must be at most 10.', ret)

    def test__colloquialize_validation_error_attribute_name_at_end_of_message(self):
        message = "Bad value for field integer"
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Bad value for field Integer', ret)

    def test__colloquialize_validation_error_attribute_name_at_beginning_and_end_of_message(self):
        message = "integer must be an integer"
        attribute_name = 'integer'
        attribute_title = 'Integer'

        ret = self.instance._colloquialize_validation_error(
            message=message,
            attribute_name=attribute_name,
            attribute_title=attribute_title
        )

        self.assertEqual('Integer must be an integer', ret)
