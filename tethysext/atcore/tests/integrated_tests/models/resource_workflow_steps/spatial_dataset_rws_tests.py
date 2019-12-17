from unittest import mock
import json
import pandas as pd
from .common import RWS_DEFAULT_OPTIONS
from tethysext.atcore.models.resource_workflow_steps import SpatialDatasetRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialDatasetRWSTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        m = mock.MagicMock()
        m.__reduce__ = lambda self: (mock.MagicMock, ())
        self.instance = SpatialDatasetRWS(
            name='foo',
            order=1,
            help='Lorem Ipsum',
            options={
                'geometry_source': {SpatialDatasetRWS.OPT_PARENT_STEP: 'geometry'},
                'dataset_title': 'Hydrograph',
                'template_dataset': pd.DataFrame(columns=['Time (min)', 'Discharge (cfs)']),
                'plot_columns': ('Time (min)', 'Discharge (cfs)'),
            },
            geoserver_name='',
            map_manager=m,
            spatial_manager=m

        )

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(SpatialDatasetRWS).get(self.instance.id)
        self.assertEqual(self.instance, ret)

    def test_default_options(self):
        baseline = {
            'geometry_source': None,
            'dataset_title': self.instance.DEFAULT_DATASET_TITLE,
            'template_dataset': self.instance.DEFAULT_DATASET,
            'read_only_columns': [],
            'plot_columns': [],
            'max_rows': self.instance.DEFAULT_MAX_ROWS,
            'empty_rows': self.instance.DEFAULT_EMPTY_ROWS,
            'geocode_enabled': False,
            **RWS_DEFAULT_OPTIONS
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_init_parameters(self):
        baseline = {
            'datasets': {
                'help': 'Valid JSON representing geometry input by user.',
                'value': None,
                'required': False
            },
        }
        self.assertDictEqual(baseline, self.instance.init_parameters())

    @mock.patch(
        'tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws.SpatialDatasetRWS.resolve_option')  # noqa: E501
    @mock.patch(
        'tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws.SpatialResourceWorkflowStep.validate')  # noqa: E501
    def test_validate(self, mock_validate, mock_resolve_option):
        base_geom = {'features': [{'properties': {'bad_id_key': '01'}, }, {'properties': {'id': '02'}, },
                                  {'properties': {'id': '03'}, }]}  # noqa: E501
        mock_resolve_option.return_value = base_geom
        self.assertRaises(ValueError, self.instance.validate)
        mock_validate.assert_called()

    @mock.patch(
        'tethysext.atcore.models.resource_workflow_steps.spatial_dataset_rws.SpatialResourceWorkflowStep.to_dict')  # noqa: E501
    def test_to_dict(self, mock_to_dict):
        baseline = {'type': 'spatial_dataset_workflow_step',
                    'name': 'foo',
                    'help': 'Lorem Ipsum',
                    'parameters':
                        {'datasets': {
                            'feature_id_01': {0: ['data_01']},
                            'feature_id_02': {0: ['data_02']},
                            'feature_id_03': {0: ['data_03']},
                            'feature_id_04': {0: ['data_04']},
                            'feature_id_05': {0: ['data_05']}
                        }}
                    }
        data = {'feature_id_01': pd.DataFrame(['data_01']),
                'feature_id_02': pd.DataFrame(['data_02']),
                'feature_id_03': pd.DataFrame(['data_03']),
                'feature_id_04': pd.DataFrame(['data_04']),
                'feature_id_05': pd.DataFrame(['data_05'])}
        mock_to_dict.return_value = {'type': 'spatial_dataset_workflow_step', 'name': 'foo', 'help': 'Lorem Ipsum',
                                     'parameters': {'datasets': data}}
        ret = self.instance.to_dict()
        self.assertDictEqual(baseline, ret)

    def test_to_geojson(self):
        geojson_dict = {
            'type': 'FeatureCollection',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                            [[-87.90161132812499, 30.66072872520222], [-87.89594650268555, 30.662943651723793],
                             [-87.89457321166992, 30.655117350832413], [-87.90023803710938, 30.658070746371095],
                             [-87.90161132812499, 30.66072872520222]]]},
                'properties': {
                    'id': 1
                }
            }]
        }

        serialized_step = {
            'name': 'Define Hydrographs',
            'resource_workflow_id': '8d49392b-8b2e-4136-bbd5-da1514cb2031',
            'child_id': 'None',
            'id': 'f0eacad1-a707-4ee2-8a2a-8c6869474769',
            'help': 'Define hydrographs for each of the new detention basins.',
            'type': 'spatial_dataset_workflow_step',
            'parameters': {
                'datasets': {
                    '1': {
                        'Time (min)': [0.0, 60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0, 600.0, 660.0,
                                       720.0, 780.0, 840.0, 900.0, 960.0, 1020.0],
                        'Discharge (cfs)': [0.0, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0, 42.0, 56.0, 70.0, 62.0, 53.0, 36.0,
                                            18.0, 12.0, 6.0, 3.0, 0.0]}
                }
            }
        }

        self.instance.resolve_option = mock.MagicMock(return_value=geojson_dict)
        self.instance.to_dict = mock.MagicMock(return_value=serialized_step)
        ret = self.instance.to_geojson(as_str=False)

        baseline = {
            'type': 'FeatureCollection',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [[-87.90161132812499, 30.66072872520222],
                         [-87.89594650268555, 30.662943651723793],
                         [-87.89457321166992, 30.655117350832413],
                         [-87.90023803710938, 30.658070746371095],
                         [-87.90161132812499, 30.66072872520222]]]},
                    'properties': {
                        'id': 1,
                        'hydrograph': {
                            'type': 'dataset',
                            'value': {
                                'Time (min)': [0.0, 60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0,
                                               600.0, 660.0, 720.0, 780.0, 840.0, 900.0, 960.0, 1020.0],
                                'Discharge (cfs)': [0.0, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0, 42.0, 56.0, 70.0, 62.0, 53.0,
                                                    36.0, 18.0, 12.0, 6.0, 3.0, 0.0],
                                'meta': {
                                    'columns': ['Time (min)', 'Discharge (cfs)'],
                                    'length': 18}
                            }
                        }
                    }
            }]
        }
        self.assertEqual(baseline, ret)

    def test_to_geojson_str(self):
        geojson_dict = {
            'type': 'FeatureCollection',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [[-87.90161132812499, 30.66072872520222], [-87.89594650268555, 30.662943651723793],
                         [-87.89457321166992, 30.655117350832413], [-87.90023803710938, 30.658070746371095],
                         [-87.90161132812499, 30.66072872520222]]]},
                'properties': {
                    'id': 1
                }
            }]
        }

        serialized_step = {
            'name': 'Define Hydrographs',
            'resource_workflow_id': '8d49392b-8b2e-4136-bbd5-da1514cb2031',
            'child_id': 'None',
            'id': 'f0eacad1-a707-4ee2-8a2a-8c6869474769',
            'help': 'Define hydrographs for each of the new detention basins.',
            'type': 'spatial_dataset_workflow_step',
            'parameters': {
                'datasets': {
                    '1': {
                        'Time (min)': [0.0, 60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0, 600.0, 660.0,
                                       720.0, 780.0, 840.0, 900.0, 960.0, 1020.0],
                        'Discharge (cfs)': [0.0, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0, 42.0, 56.0, 70.0, 62.0, 53.0, 36.0,
                                            18.0, 12.0, 6.0, 3.0, 0.0]}
                }
            }
        }

        self.instance.resolve_option = mock.MagicMock(return_value=geojson_dict)
        self.instance.to_dict = mock.MagicMock(return_value=serialized_step)
        ret = self.instance.to_geojson(as_str=True)

        baseline = {
            'type': 'FeatureCollection',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [[-87.90161132812499, 30.66072872520222],
                         [-87.89594650268555, 30.662943651723793],
                         [-87.89457321166992, 30.655117350832413],
                         [-87.90023803710938, 30.658070746371095],
                         [-87.90161132812499, 30.66072872520222]]]},
                'properties': {
                    'id': 1,
                    'hydrograph': {
                        'type': 'dataset',
                        'value': {
                            'Time (min)': [0.0, 60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0,
                                           600.0, 660.0, 720.0, 780.0, 840.0, 900.0, 960.0, 1020.0],
                            'Discharge (cfs)': [0.0, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0, 42.0, 56.0, 70.0, 62.0, 53.0,
                                                36.0, 18.0, 12.0, 6.0, 3.0, 0.0],
                            'meta': {
                                'columns': ['Time (min)', 'Discharge (cfs)'],
                                'length': 18}
                        }
                    }
                }
            }]
        }
        baseline = json.dumps(baseline)
        self.assertEqual(baseline, ret)
