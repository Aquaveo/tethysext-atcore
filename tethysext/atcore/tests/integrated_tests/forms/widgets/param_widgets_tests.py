"""
********************************************************************************
* Name: param_widgets_tests.py
* Author: mlebaron
* Created On: September 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import param
import unittest
from unittest import mock
# from tethysext.atcore.forms.widgets import param_widgets as widgets


class ParamWidgetsTests(unittest.TestCase):

    def setUp(self):
        name = param.parameterized.String('the_name')
        location_name = param.parameterized.String('the_location_name')

        self.parameterized_obj = mock.MagicMock(
            name=mock.MagicMock(
                title=mock.MagicMock()
            ),
            params=mock.MagicMock()
        )
        self.parameterized_obj.name.title.return_value = 'form_title'
        self.parameterized_obj.params.return_value = {'name': name, 'location_name': location_name}

    def tearDown(self):
        pass

    def test_generate_django_form_no_params(self):
        pass
        # form = widgets.generate_django_form(self.parameterized_obj)
        #
        # param_data = form.base_fields[None]
        # self.assertEqual('This field is required.', param_data.error_messages['required'])
        # self.assertEqual('the_location_name', param_data.initial)
