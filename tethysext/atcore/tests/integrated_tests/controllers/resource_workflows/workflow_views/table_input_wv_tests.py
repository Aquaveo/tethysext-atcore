"""
********************************************************************************
* Name: spatial_dataset_mwv_tests.py
* Author: nswain
* Created On: June 8, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
from unittest import mock
import pandas as pd
from django.http import HttpRequest, HttpResponseRedirect, QueryDict
from tethysext.atcore.controllers.resource_workflows.workflow_views import TableInputWV
from tethysext.atcore.models.resource_workflow_steps.table_input_rws import TableInputRWS
from tethysext.atcore.tests.integrated_tests.controllers.resource_workflows.workflow_view_test_case import \
    WorkflowViewTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TableInputWVTests(WorkflowViewTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.GET = {'feature_id': 'feature1'}
        self.request.POST = QueryDict('next-submit', mutable=True)
        self.request.method = 'method1'
        self.request.path = 'path'
        self.request.META = {}
        self.request.user = mock.MagicMock(is_authenticated=True, is_active=True)
        self.back_url = './back'
        self.next_url = './next'
        self.current_url = './current'

        self.step = TableInputRWS(
            name="Test Table Input View Step",
            help="This is a test step to aid testing the Table Input View.",
            order=1,
            options={},
        )
        self.workflow.steps.append(self.step)

        self.session.commit()

        step_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_step')
        self.mock_get_step = step_patcher.start()
        self.addCleanup(step_patcher.stop)
        self.mock_get_step.return_value = self.step

        workflow_patcher = mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_workflow')  # noqa: E501
        self.mock_get_workflow = workflow_patcher.start()
        self.addCleanup(workflow_patcher.stop)
        self.mock_get_workflow.return_value = self.workflow

        self.maxDiff = None

    def tearDown(self):
        super().tearDown()

    def tests_process_step_options_default_options(self):
        self.step.options = {}  # Don't specify any options
        context = {}

        TableInputWV().process_step_options(
            self.request, self.session, context, self.resource, self.step, None, None
        )

        self.assertDictEqual(context.get('column_is_numeric'), {'X': True, 'Y': True})
        self.assertEqual(context.get('dataset_title'), 'Dataset')
        self.assertEqual(context.get('max_rows'), 1000)
        self.assertEqual(context.get('optional_columns'), [])
        self.assertEqual(context.get('plot_columns'), [])
        self.assertEqual(context.get('read_only_columns'), [])
        self.assertEqual(len(context.get('rows')), 10)
        self.assertListEqual(context.get('columns').tolist(), ['X', 'Y'])
        self.assertEqual(context.get('nodata_val'), -99999.9)

    def tests_process_step_options_custom_options(self):
        self.step.options = {
            'dataset_title': 'Test Table Input Dataset',
            'template_dataset': pd.DataFrame(columns=['D', 'E', 'F', 'G']),
            'read_only_columns': ['D'],
            'plot_columns': ['E', 'F'],
            'optional_columns': ['G'],
            'max_rows': 500,
            'empty_rows': 5
        }
        context = {}

        TableInputWV().process_step_options(
            self.request, self.session, context, self.resource, self.step, None, None
        )

        self.assertDictEqual(context.get('column_is_numeric'), {'D': True, 'E': True, 'F': True, 'G': True})
        self.assertEqual(context.get('dataset_title'), 'Test Table Input Dataset')
        self.assertEqual(context.get('max_rows'), 500)
        self.assertEqual(context.get('optional_columns'), ['G'])
        self.assertEqual(context.get('plot_columns'), ['E', 'F'])
        self.assertEqual(context.get('read_only_columns'), ['D'])
        self.assertEqual(len(context.get('rows')), 5)
        self.assertListEqual(context.get('columns').tolist(), ['D', 'E', 'F', 'G'])
        self.assertEqual(context.get('nodata_val'), -99999.9)

    def tests_process_step_options_empty_gt_max(self):
        self.step.options = {
            'max_rows': 3,
            'empty_rows': 5,  # greater than max_rows
        }
        context = {}

        TableInputWV().process_step_options(
            self.request, self.session, context, self.resource, self.step, None, None
        )

        self.assertDictEqual(context.get('column_is_numeric'), {'X': True, 'Y': True})
        self.assertEqual(context.get('dataset_title'), 'Dataset')
        self.assertEqual(context.get('max_rows'), 3)
        self.assertEqual(context.get('optional_columns'), [])
        self.assertEqual(context.get('plot_columns'), [])
        self.assertEqual(context.get('read_only_columns'), [])
        self.assertEqual(len(context.get('rows')), 3)  # Should be max_rows
        self.assertListEqual(context.get('columns').tolist(), ['X', 'Y'])
        self.assertEqual(context.get('nodata_val'), -99999.9)

    def tests_process_step_options_template_dataset_func(self):
        def dataset_func(request, session, resource, step, *args, **kwargs):
            self.assertIs(request, self.request)
            self.assertIs(session, self.session)
            self.assertIs(resource, self.resource)
            self.assertIs(step, self.step)
            self.assertEqual(args, ())
            self.assertDictEqual(kwargs, {})
            return pd.DataFrame(columns=['H', 'I', 'J'])

        self.step.options = {
            'template_dataset': dataset_func
        }
        context = {}

        TableInputWV().process_step_options(
            self.request, self.session, context, self.resource, self.step, None, None
        )

        self.assertDictEqual(context.get('column_is_numeric'), {'H': True, 'I': True, 'J': True})
        self.assertEqual(context.get('dataset_title'), 'Dataset')
        self.assertEqual(context.get('max_rows'), 1000)
        self.assertEqual(context.get('optional_columns'), [])
        self.assertEqual(context.get('plot_columns'), [])
        self.assertEqual(context.get('read_only_columns'), [])
        self.assertEqual(len(context.get('rows')), 10)
        self.assertListEqual(context.get('columns').tolist(), ['H', 'I', 'J'])
        self.assertEqual(context.get('nodata_val'), -99999.9)

    def tests_process_step_options_load_saved_dataset(self):
        self.step.options = {}  # Don't specify any options
        saved_dataset = pd.DataFrame({'X': [1, 2, 3, 4, 5], 'Y': [2, 4, 6, 8, 10]})
        self.step.set_parameter('dataset', saved_dataset.to_dict(orient='list'))
        context = {}

        TableInputWV().process_step_options(
            self.request, self.session, context, self.resource, self.step, None, None
        )

        self.assertDictEqual(context.get('column_is_numeric'), {'X': True, 'Y': True})
        self.assertEqual(context.get('dataset_title'), 'Dataset')
        self.assertEqual(context.get('max_rows'), 1000)
        self.assertEqual(context.get('optional_columns'), [])
        self.assertEqual(context.get('plot_columns'), [])
        self.assertEqual(context.get('read_only_columns'), [])
        self.assertEqual(len(context.get('rows')), 5)
        self.assertListEqual(context.get('rows'), [
            {'X': 1, 'Y': 2},
            {'X': 2, 'Y': 4},
            {'X': 3, 'Y': 6},
            {'X': 4, 'Y': 8},
            {'X': 5, 'Y': 10}
        ])
        self.assertListEqual(context.get('columns').tolist(), ['X', 'Y'])
        self.assertEqual(context.get('nodata_val'), -99999.9)

    def test_process_step_data(self):
        template_dataset = pd.DataFrame({
            'D': ['one', 'two', 'three', 'four', 'five'],
            'E': [1, None, None, None, None],
            'F': [2.0, None, None, None, None],
            'G': ['', '', '', '', ''],
        })
        self.step.options = {
            'dataset_title': 'Test Table Input Dataset',
            'template_dataset': template_dataset,
            'read_only_columns': ['D'],
            'plot_columns': ['E', 'F'],
            'optional_columns': ['G'],
            'max_rows': 10,
            'empty_rows': 5
        }
        submitted_data = {
            'D': ['one', 'two', 'three', 'four', 'five'],
            'E': ['1', '2', '3', '4', '5'],
            'F': ['2.0', '4.0', '6.0', '8.0', '10.0'],
            'G': ['', '', '', '', ''],
        }
        for k, v in submitted_data.items():
            self.request.POST.setlist(k, v)

        ret = TableInputWV().process_step_data(
            self.request, self.session, self.step, self.resource, self.current_url, self.back_url, self.next_url
        )

        d = self.step.get_parameter('dataset')
        self.assertDictEqual(d, {
            'D': ['one', 'two', 'three', 'four', 'five'],
            'E': [1.0, 2.0, 3.0, 4.0, 5.0],
            'F': [2.0, 4.0, 6.0, 8.0, 10.0],
            'G': [-99999.9, -99999.9, -99999.9, -99999.9, -99999.9]
        })
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(ret.url, self.next_url)

    def test_process_step_data_template_dataset_func(self):
        def dataset_func(request, session, resource, step, *args, **kwargs):
            self.assertIs(request, self.request)
            self.assertIs(session, self.session)
            self.assertIs(resource, self.resource)
            self.assertIs(step, self.step)
            self.assertEqual(args, ())
            self.assertDictEqual(kwargs, {})
            return pd.DataFrame({
                'D': ['one', 'two', 'three', 'four', 'five'],
                'E': [1, None, None, None, None],
                'F': [2.0, None, None, None, None],
                'G': [4, None, None, None, None],
            })
        self.step.options = {
            'dataset_title': 'Test Table Input Dataset',
            'template_dataset': dataset_func,
            'read_only_columns': ['D'],
            'plot_columns': ['E', 'F'],
            'optional_columns': ['G'],
            'max_rows': 10,
            'empty_rows': 5
        }
        submitted_data = {
            'D': ['one', 'two', 'three', 'four', 'five'],
            'E': ['1', '2', '3', '4', '5'],
            'F': ['2.0', '4.0', '6.0', '8.0', '10.0'],
            'G': ['4', '8', '16', '32', '64'],
        }
        for k, v in submitted_data.items():
            self.request.POST.setlist(k, v)

        ret = TableInputWV().process_step_data(
            self.request, self.session, self.step, self.resource, self.current_url, self.back_url, self.next_url
        )

        d = self.step.get_parameter('dataset')
        self.assertDictEqual(d, {
            'D': ['one', 'two', 'three', 'four', 'five'],
            'E': [1.0, 2.0, 3.0, 4.0, 5.0],
            'F': [2.0, 4.0, 6.0, 8.0, 10.0],
            'G': [4.0, 8.0, 16.0, 32.0, 64.0]
        })
        self.assertIsInstance(ret, HttpResponseRedirect)
        self.assertEqual(ret.url, self.next_url)
