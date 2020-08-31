import unittest
from tethysext.atcore.mixins import OptionsMixin


class ClassWithOptions(OptionsMixin):
    _options = None


class OptionsMixinTests(unittest.TestCase):

    def setUp(self):
        self.instance = ClassWithOptions()

        # Merge tests
        self.a = {
            'merge-0': {
                'conflict-1': True,
                'merge-1': {
                    'a-2': 1
                },
                'a-1': 1
            },
            'conflict-0': 1,
            'a-0': 1
        }

        self.b = {
            'merge-0': {
                'conflict-1': False,
                'merge-1': {
                    'b-2': 2
                },
                'b-1': 2
            },
            'conflict-0': 2,
            'b-0': 2
        }

        self.a_on_b = {
            'merge-0': {
                'conflict-1': True,
                'merge-1': {
                    'a-2': 1,
                    'b-2': 2
                },
                'a-1': 1,
                'b-1': 2
            },
            'conflict-0': 1,
            'a-0': 1,
            'b-0': 2
        }

        self.b_on_a = {
            'merge-0': {
                'conflict-1': False,
                'merge-1': {
                    'a-2': 1,
                    'b-2': 2
                },
                'a-1': 1,
                'b-1': 2
            },
            'conflict-0': 2,
            'a-0': 1,
            'b-0': 2
        }

        self.a_none = {
            'merge-0': None,
            'conflict-0': 1,
            'a-0': 1
        }

        self.b_on_a_none = {
            'merge-0': {
                'conflict-1': False,
                'merge-1': {
                    'b-2': 2
                },
                'b-1': 2
            },
            'conflict-0': 2,
            'a-0': 1,
            'b-0': 2
        }

    def tearDown(self):
        pass

    def test_default_options(self):
        self.assertDictEqual({}, self.instance.default_options)

    def test_options(self):
        baseline = {'foo': 1, 'bar': 2, 'baz': 3}
        self.instance._options = baseline
        self.assertDictEqual(baseline, self.instance.options)

    def test_options_setter(self):
        baseline = {'foo': 1, 'bar': 2, 'baz': 3}
        self.instance._options = {'key_to_remove': 4}
        self.instance.options = baseline
        self.assertDictEqual(baseline, self.instance._options)

    def test_options_setter_error(self):
        try:
            self.instance.options = 'bad value'
        except Exception as e:
            self.assertIsInstance(e, ValueError)

        try:
            self.instance.options = None
        except Exception as e:
            self.assertIsInstance(e, ValueError)

    def test__merge_options_b_on_a(self):
        ret = self.instance._merge_options(self.a, self.b)
        self.assertEqual(self.b_on_a, ret)

    def test__merge_options_a_on_b(self):
        ret = self.instance._merge_options(self.b, self.a)
        self.assertEqual(self.a_on_b, ret)

    def test__merge_options_both_ways(self):
        """
        Ensures there is no funny business w/ references to the dictionaries being passed...
        """
        ret1 = self.instance._merge_options(self.a, self.b)
        self.assertEqual(self.b_on_a, ret1)

        ret2 = self.instance._merge_options(self.b, self.a)
        self.assertEqual(self.a_on_b, ret2)

        self.assertNotEqual(ret1, ret2)

    def test__merge_options_none_for_dict(self):
        ret = self.instance._merge_options(self.a_none, self.b)
        self.assertEqual(self.b_on_a_none, ret)
