from unittest import mock
import pandas as pd
from tethysext.atcore.models.resource_workflow_steps import TableInputRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TableInputRWSTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        m = mock.MagicMock()
        m.__reduce__ = lambda self: (mock.MagicMock, ())
        self.template_dataset = pd.DataFrame(columns=['A', 'B', 'C'])
        self.instance = TableInputRWS(
            name='foo table',
            order=1,
            help='Lorem Ipsum table',
            options={
                'dataset_title': 'Test Dataset',
                'template_dataset': self.template_dataset,
                'read_only_columns': ['B'],
                'plot_columns': ['C'],
                'optional_columns': ['A'],
                'max_rows': 200,
                'empty_rows': 20
            },
        )

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(TableInputRWS).get(self.instance.id)
        self.assertEqual(self.instance, ret)
        self.session.delete(self.instance)
        self.session.commit()

    def test_default_options(self):
        baseline = {
            'dataset_title': TableInputRWS.DEFAULT_DATASET_TITLE,
            'template_dataset': TableInputRWS.DEFAULT_DATASET,
            'read_only_columns': [],
            'plot_columns': [],
            'optional_columns': [],
            'max_rows': TableInputRWS.DEFAULT_MAX_ROWS,
            'empty_rows': TableInputRWS.DEFAULT_EMPTY_ROWS,
            'fixed_rows': TableInputRWS.DEFAULT_FIXED_ROWS,
            'release_resource_lock_on_completion': True,
            'release_resource_lock_on_init': False,
            'release_workflow_lock_on_completion': True,
            'release_workflow_lock_on_init': False,
            'resource_lock_required': False,
            'workflow_lock_required': False,
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_init_parameters(self):
        baseline = {
            'dataset': {
                'help': 'Valid JSON representing datasets input by user.',
                'value': None,
                'required': False
            },
        }
        self.assertDictEqual(baseline, self.instance.init_parameters())

    def test_validate(self):
        with self.assertRaises(ValueError):
            self.instance.validate()
