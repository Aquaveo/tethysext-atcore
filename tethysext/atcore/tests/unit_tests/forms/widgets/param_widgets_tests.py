"""
********************************************************************************
* Name: param_widgets_tests.py
* Author: mlebaron
* Created On: September 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import unittest
from unittest import mock
from tethysext.atcore.forms.widgets import param_widgets as widgets


class ParamWidgetsTests(unittest.TestCase):

    def setUp(self):
        self.parameterized_obj = mock.MagicMock(
            name=mock.MagicMock(
                title=mock.MagicMock(
                    return_value='form_title'
                )
            ),
            params=mock.MagicMock(
                return_value=[]
            )
        )

    def tearDown(self):
        pass
