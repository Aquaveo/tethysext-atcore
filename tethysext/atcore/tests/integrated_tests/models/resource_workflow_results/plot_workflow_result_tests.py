from unittest import mock
import pandas as pd
from tethysext.atcore.models.resource_workflow_results import PlotWorkflowResult
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class PlotWorkflowResultTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = PlotWorkflowResult(name='test')

    def bind_instance_to_session(self):
        self.session.add(self.instance)
        self.session.commit()

    def test_default_options(self):
        baseline = {
            'plot_kwargs': {
                'plot_lib': 'bokeh',
            },
            'no_dataset_message': 'No dataset found.'
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_datasets(self):
        self.assertDictEqual({}, self.instance.data)
        ret = self.instance.datasets
        self.assertListEqual([], ret)

    def test_reset(self):
        self.instance.data['datasets'] = 'Bad data to reset'
        self.instance.reset()
        ret = self.instance.data['datasets']
        self.assertEqual([], ret)

    def test__add_dataset(self):
        test_data = 'Test data'
        self.instance._add_dataset(test_data)
        self.assertListEqual([test_data], self.instance.datasets)

    def test_datasets_bound(self):
        self.bind_instance_to_session()
        self.test_datasets()

    def test_reset_datasets_bound(self):
        self.bind_instance_to_session()
        self.test_reset()

    def test__add_dataset_bound(self):
        self.bind_instance_to_session()
        self.test__add_dataset()

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult._add_dataset')  # noqa: E501
    def test_add_pandas_dataframe(self, mock_add_dataset):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=False)
        self.instance.add_pandas_dataframe('foo', mock_dataframe)
        baseline = {
            'title': 'foo',
            'dataset': mock_dataframe,
        }
        mock_add_dataset.assert_called_with(baseline)

    def test_add_pandas_dataframe_no_title(self):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=False)
        self.assertRaises(ValueError, self.instance.add_pandas_dataframe, '', mock_dataframe)
        self.assertRaises(ValueError, self.instance.add_pandas_dataframe, None, mock_dataframe)

    def test_add_pandas_dataframe_not_dataframe(self):
        self.assertRaises(ValueError, self.instance.add_pandas_dataframe, 'foo', ['test'])

    def test_add_pandas_dataframe_empty_dataframe(self):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=True)
        self.assertRaises(ValueError, self.instance.add_pandas_dataframe, 'foo', mock_dataframe)
