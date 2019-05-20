import unittest
from tethysext.atcore.mixins import OptionsMixin


class ClassWithOptions(OptionsMixin):
    _options = None


class OptionsMixinTests(unittest.TestCase):

    def setUp(self):
        self.instance = ClassWithOptions()

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
