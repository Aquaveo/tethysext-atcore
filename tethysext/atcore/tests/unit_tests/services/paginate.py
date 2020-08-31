import unittest
from tethysext.atcore.services.paginate import paginate


class PaginateTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_num_objects_lt_result_per_page(self):
        objects = range(7)
        results_per_page = 10
        page = 1
        result_name = 'foos'
        paginated_objects, pagination_info = paginate(objects, results_per_page, page, result_name)
        self.assertEqual(objects, paginated_objects)
        self.assertEqual(len(objects), pagination_info['num_results'])
        self.assertEqual(result_name, pagination_info['result_name'])
        self.assertEqual(page, pagination_info['page'])
        self.assertEqual(page + 1, pagination_info['next_page'])
        self.assertEqual(page - 1, pagination_info['previous_page'])
        self.assertFalse(pagination_info['enable_next_button'])
        self.assertFalse(pagination_info['enable_previous_button'])
        self.assertTrue(pagination_info['hide_buttons'])
        self.assertTrue(pagination_info['hide_header_buttons'])
        self.assertEqual(results_per_page, pagination_info['show'])
        self.assertEqual([5], pagination_info['results_per_page_options'])
        self.assertFalse(pagination_info['hide_results_per_page_options'])

    def test_num_objects_gt_result_per_page(self):
        objects = range(42)
        results_per_page = 40
        page = 1
        result_name = 'foos'
        paginated_objects, pagination_info = paginate(objects, results_per_page, page, result_name)
        self.assertEqual(objects[:40], paginated_objects)
        self.assertEqual(len(objects), pagination_info['num_results'])
        self.assertEqual(result_name, pagination_info['result_name'])
        self.assertEqual(page, pagination_info['page'])
        self.assertEqual(page + 1, pagination_info['next_page'])
        self.assertEqual(page - 1, pagination_info['previous_page'])
        self.assertTrue(pagination_info['enable_next_button'])
        self.assertFalse(pagination_info['enable_previous_button'])
        self.assertFalse(pagination_info['hide_buttons'])
        self.assertFalse(pagination_info['hide_header_buttons'])
        self.assertEqual(results_per_page, pagination_info['show'])
        self.assertEqual([5, 10, 20, 40], pagination_info['results_per_page_options'])
        self.assertFalse(pagination_info['hide_results_per_page_options'])

    def test_num_objects_gt_result_per_page_second(self):
        objects = range(42)
        results_per_page = 40
        page = 2
        result_name = 'foos'
        paginated_objects, pagination_info = paginate(objects, results_per_page, page, result_name)
        self.assertEqual(objects[40:], paginated_objects)
        self.assertEqual(len(objects), pagination_info['num_results'])
        self.assertEqual(result_name, pagination_info['result_name'])
        self.assertEqual(page, pagination_info['page'])
        self.assertEqual(page + 1, pagination_info['next_page'])
        self.assertEqual(page - 1, pagination_info['previous_page'])
        self.assertFalse(pagination_info['enable_next_button'])
        self.assertTrue(pagination_info['enable_previous_button'])
        self.assertFalse(pagination_info['hide_buttons'])
        self.assertTrue(pagination_info['hide_header_buttons'])
        self.assertEqual(results_per_page, pagination_info['show'])
        self.assertEqual([5, 10, 20, 40], pagination_info['results_per_page_options'])
        self.assertFalse(pagination_info['hide_results_per_page_options'])

    def test_num_objects_eq_result_per_page(self):
        objects = range(120)
        results_per_page = 120
        page = 1
        result_name = 'foos'
        paginated_objects, pagination_info = paginate(objects, results_per_page, page, result_name)
        self.assertEqual(objects, paginated_objects)
        self.assertEqual(len(objects), pagination_info['num_results'])
        self.assertEqual(result_name, pagination_info['result_name'])
        self.assertEqual(page, pagination_info['page'])
        self.assertEqual(page + 1, pagination_info['next_page'])
        self.assertEqual(page - 1, pagination_info['previous_page'])
        self.assertFalse(pagination_info['enable_next_button'])
        self.assertFalse(pagination_info['enable_previous_button'])
        self.assertTrue(pagination_info['hide_buttons'])
        self.assertFalse(pagination_info['hide_header_buttons'])
        self.assertEqual(results_per_page, pagination_info['show'])
        self.assertEqual([5, 10, 20, 40, 80, 120], pagination_info['results_per_page_options'])
        self.assertFalse(pagination_info['hide_results_per_page_options'])
