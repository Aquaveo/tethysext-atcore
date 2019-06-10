from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowResult


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowResultTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        # Custom setup here
        #  Build the workflow
        self.workflow = ResourceWorkflow(name='bar')

        #  Build the result to test
        self.result = ResourceWorkflowResult(name='foo', description='lorem_1', _data={'baz': 1})

        # Add the result to the workflow
        self.workflow.results = [self.result]

        self.session.add(self.workflow)
        self.session.commit()

    def test__init__options_in_kwargs(self):
        baseline_options = {'foo': 0, 'bar': 1, 'baz': 3}
        result = ResourceWorkflowResult(name='foo', description='lorem_1', _data={'baz': 1}, options=baseline_options)
        self.assertDictEqual(baseline_options, result.options)

    def test__str__(self):
        baseline_str = '<ResourceWorkflowResult name="{}" id="{}" >'.format(self.result.name, self.result.id)
        ret = str(self.result)
        self.assertEqual(baseline_str, ret)

    def test__repr__(self):
        baseline_repr_str = '<ResourceWorkflowResult name="{}" id="{}" >'.format(self.result.name, self.result.id)
        ret = repr(self.result)

        # Make sure we get the proper string.
        self.assertEqual(baseline_repr_str, ret)

    def test_controller(self):
        ret = self.result.controller
        self.assertEqual(self.result._controller, ret)

    def test_data_getter(self):
        ret = self.result.data
        self.assertDictEqual({'baz': 1}, ret)

    def test_data_getter_empty(self):
        no_data_result = ResourceWorkflowResult(name='foo')
        ret = no_data_result.data
        self.assertDictEqual({}, ret)

    def test_data_setter(self):
        new_data = {'foo': 2}
        self.result.data = new_data
        self.assertDictEqual(new_data, self.result._data)

    def test_data_setter_empty(self):
        new_data = {'foo': 2}
        no_data_result = ResourceWorkflowResult(name='foo')
        no_data_result.data = new_data
        self.assertDictEqual(new_data, no_data_result._data)

    def test_data_setter_bound(self):
        self.session.add(self.result)
        self.session.commit()
        new_data = {'bar': 3}
        self.result.data = new_data
        self.assertDictEqual(new_data, self.result._data)
