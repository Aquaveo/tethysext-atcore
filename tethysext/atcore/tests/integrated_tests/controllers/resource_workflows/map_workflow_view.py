"""
********************************************************************************
* Name: map_workflow_view.py
* Author: Teva, Tanner
* Created On: December 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.tests.factories.django_user import UserFactory


class MapWorkflowViewTests(TethysTestCase):

    def setUp(self):
        self.user = UserFactory()
        self.request_factory = RequestFactory()

    def tearDown(self):
        pass

    def test_get_context(self):
        pass
