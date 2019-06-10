from unittest import mock
from tethysext.atcore.models.resource_workflow_results import SpatialWorkflowResult
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialWorkflowResultTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = SpatialWorkflowResult(
            name='test',
            geoserver_name='geoserver_name',
            map_manager='map_manager',
            spatial_manager='spatial_manager'
        )

    def bind_instance_to_session(self):
        self.session.add(self.instance)
        self.session.commit()

    def test_default_options(self):
        baseline = {
            'layer_group_title': 'Results',
            'layer_group_control': 'checkbox'
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_layers(self):
        self.assertDictEqual({}, self.instance.data)
        ret = self.instance.layers
        self.assertListEqual([], ret)

    def test_clear_layers(self):
        self.instance.data['layers'] = 'Bad data to clear'
        self.instance.clear_layers()
        ret = self.instance.data['layers']
        self.assertEqual([], ret)

    def test_layers_bound(self):
        self.bind_instance_to_session()
        self.test_layers()

    def test_clear_layers_bound(self):
        self.bind_instance_to_session()
        self.test_clear_layers()

    def prepare_layers(self, with_layer_ids=True):
        self.layer_1 = {'layer_name': 'foo'}  # with_layer_ids: 'layer_id': 1
        self.layer_2 = {'layer_name': 'bar'}  # with_layer_ids: 'layer_id': 2
        self.layer_3 = {'layer_name': 'baz'}  # with_layer_ids: 'layer_id': 3

        layers = [self.layer_1, self.layer_2, self.layer_3]

        if with_layer_ids:
            for index, layer in enumerate(layers):
                layer['layer_id'] = index + 1

        return layers

    def test_get_layer_with_layer_id(self):
        layers = self.prepare_layers(with_layer_ids=True)
        self.instance.layers = layers
        ret = self.instance.get_layer(3)
        self.assertDictEqual(self.layer_3, ret)

    def test_get_layer_without_layer_id(self):
        layers = self.prepare_layers(with_layer_ids=False)
        self.instance.layers = layers
        ret = self.instance.get_layer('bar')
        self.assertDictEqual(self.layer_2, ret)

    def test_get_layer_not_found(self):
        layers = self.prepare_layers(with_layer_ids=True)
        self.instance.layers = layers
        ret = self.instance.get_layer(4)
        self.assertIsNone(ret)

    def test__add_layer(self):
        self.prepare_layers(with_layer_ids=True)
        self.assertListEqual([], self.instance.layers)
        self.instance._add_layer(self.layer_1)
        self.assertEqual(1, len(self.instance.layers))
        self.assertDictEqual(self.layer_1, self.instance.layers[0])

    @mock.patch('tethysext.atcore.models.resource_workflow_results.spatial_workflow_result.SpatialWorkflowResult._add_layer')  # noqa: E501
    def test_add_geojson_layer(self, mock_add_layer):
        kwargs = dict(
            geojson={},
            layer_name='foo',
            layer_title='Foo',
            layer_variable='foos',
            layer_id='1',
            visible=False,
            public=False,
            selectable=True,
            plottable=True,
            has_action=True,
            extent=[-1, -1, 1, 1],
            popup_title='A Foo',
            excluded_properties=['a', 'b']
        )

        self.instance.add_geojson_layer(**kwargs)

        kwargs['type'] = 'geojson'

        mock_add_layer.assert_called_with(kwargs)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.spatial_workflow_result.SpatialWorkflowResult._add_layer')  # noqa: E501
    def test_add_wms_layer(self, mock_add_layer):
        kwargs = dict(
            endpoint='https://geoserver.foo.com/geoserver/wms',
            layer_name='foo',
            layer_title='Foo',
            layer_variable='foos',
            layer_id='1',
            viewparams='foo:bar,goo:jar',
            env='a:b,c:d',
            visible=False,
            public=False,
            tiled=False,
            selectable=True,
            plottable=True,
            has_action=True,
            extent=[-1, -1, 1, 1],
            popup_title='A Foo',
            excluded_properties=['a', 'b'],
            geometry_attribute='the_geom'
        )

        self.instance.add_wms_layer(**kwargs)

        kwargs['type'] = 'wms'

        mock_add_layer.assert_called_with(kwargs)
