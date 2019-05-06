import unittest
from unittest import mock
from tethysext.atcore.mixins.results_mixin import ResultsMixin


class ClassWithResults(ResultsMixin):
    results = []


class ResultMixinTests(unittest.TestCase):

    def setUp(self):
        self.instance = ClassWithResults()
        self.result_1 = mock.MagicMock(id='1')
        self.result_2 = mock.MagicMock(id='2')
        self.result_3 = mock.MagicMock(id='3')
        self.all_results = [self.result_1, self.result_2, self.result_3]

    def tearDown(self):
        del self.instance

    @mock.patch('tethysext.atcore.mixins.results_mixin.log')
    def test_get_result(self, mock_log):
        self.instance.results = self.all_results
        ret = self.instance.get_result('3')
        self.assertIs(self.result_3, ret)
        mock_log.warning.assert_not_called()

    @mock.patch('tethysext.atcore.mixins.results_mixin.log')
    def test_get_result_not_in_list(self, mock_log):
        ret = self.instance.get_result('bad_id')
        self.assertIsNone(ret)
        mock_log.warning.assert_called_with('Result with id "bad_id" not found.')

    def test_get_last_result_not_stored(self):
        self.instance.results = self.all_results
        self.instance.get_attribute = mock.MagicMock(return_value=None)
        ret = self.instance.get_last_result()
        self.assertIs(self.result_1, ret)

    def test_get_last_result_stored(self):
        self.instance.get_attribute = mock.MagicMock(return_value='2')
        self.instance.results = self.all_results
        ret = self.instance.get_last_result()
        self.assertIs(self.result_2, ret)

    @mock.patch('tethysext.atcore.mixins.results_mixin.log')
    def test_get_last_result_invalid_id_stored(self, mock_log):
        self.instance.get_attribute = mock.MagicMock(return_value='2')
        self.instance.get_result = mock.MagicMock(return_value=None)
        ret = self.instance.get_last_result()
        self.assertIsNone(ret)
        mock_log.warning.assert_called_with('Result with id "2" not found.')

    @mock.patch('tethysext.atcore.mixins.results_mixin.log')
    def test_get_last_result_workflow_has_no_results(self, mock_log):
        self.instance.get_attribute = mock.MagicMock(return_value=None)
        self.instance.results = []
        ret = self.instance.get_last_result()
        self.assertIsNone(ret)
        mock_log.warning.assert_called_with('No results found.')

    def test_set_last_result(self):
        self.instance.set_attribute = mock.MagicMock()
        self.instance.results = self.all_results
        self.instance.set_last_result(self.result_3)
        self.instance.set_attribute.assert_called_with(self.instance.ATTR_LAST_RESULT, '3')

    def test_set_last_result_invalid_result(self):
        self.instance.set_attribute = mock.MagicMock()
        self.instance.results = [self.result_1, self.result_2]
        self.assertRaises(ValueError, self.instance.set_last_result, self.result_3)

    def test_get_adjacent_results_first(self):
        self.instance.results = self.all_results
        prev_result, next_result = self.instance.get_adjacent_results(self.result_1)
        self.assertIsNone(prev_result)
        self.assertEqual(self.result_2, next_result)

    def test_get_adjacent_results_middle(self):
        self.instance.results = self.all_results
        prev_result, next_result = self.instance.get_adjacent_results(self.result_2)
        self.assertEqual(self.result_1, prev_result)
        self.assertEqual(self.result_3, next_result)

    def test_get_adjacent_results_last(self):
        self.instance.results = self.all_results
        prev_result, next_result = self.instance.get_adjacent_results(self.result_3)
        self.assertEqual(self.result_2, prev_result)
        self.assertIsNone(next_result)

    def test_get_adjacent_results_invalid_result(self):
        self.instance.results = self.all_results
        result_4 = mock.MagicMock(id='4')
        self.assertRaises(ValueError, self.instance.get_adjacent_results, result_4)
