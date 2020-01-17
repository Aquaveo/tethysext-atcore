"""
********************************************************************************
* Name: url_map_maker
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


class MockUrlMapMaker:
    """
    Mock the UrlMap meta class for testing.
    """
    def __init__(self, name, url, controller, handler=None, handler_type=None, regex=None):
        self.name = name
        self.url = url
        self.controller = controller
        self.handler = handler
        self.handler_type = handler_type
        self.regex = regex
