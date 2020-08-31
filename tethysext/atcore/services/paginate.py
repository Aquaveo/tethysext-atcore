"""
********************************************************************************
* Name: pagintate.py
* Author: nswain
* Created On: April 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


def paginate(objects, results_per_page, page, result_name, sort_by_raw=None, sort_reversed=False):
    """
    Paginate given list of objects.
    Args:
        objects(list): list of objects to paginate.
        results_per_page(int): maximum number of results to show on a page.
        page(int): page to view.
        result_name(str): name to use when referencing the objects.
        sort_by_raw(str): sort field if applicable.
        sort_reversed(boo): indicates whether the sort is reversed or not.

    Returns:
        list, dict: list of objects for current page, metadata form paginantion page.
    """
    results_per_page_options = [5, 10, 20, 40, 80, 120]
    num_objects = len(objects)
    if num_objects <= results_per_page:
        page = 1
    min_index = (page - 1) * results_per_page
    max_index = min(page * results_per_page, num_objects)
    paginated_objects = objects[min_index:max_index]
    enable_next_button = max_index < num_objects
    enable_previous_button = min_index > 0

    pagination_info = {
        'num_results': num_objects,
        'result_name': result_name,
        'page': page,
        'min_showing': min_index + 1 if max_index > 0 else 0,
        'max_showing': max_index,
        'next_page': page + 1,
        'previous_page': page - 1,
        'sort_by': sort_by_raw,
        'sort_reversed': sort_reversed,
        'enable_next_button': enable_next_button,
        'enable_previous_button': enable_previous_button,
        'hide_buttons': page == 1 and max_index == num_objects,
        'hide_header_buttons': len(paginated_objects) < 20,
        'show': results_per_page,
        'results_per_page_options': [x for x in results_per_page_options if x <= num_objects],
        'hide_results_per_page_options': num_objects <= results_per_page_options[0],
    }
    return paginated_objects, pagination_info
