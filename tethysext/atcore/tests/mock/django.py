"""
********************************************************************************
* Name: django
* Author: nswain
* Created On: April 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


class MockDjangoUser:
    def __init__(self, username, is_staff):
        self.username = username
        self.is_staff = is_staff


class MockDjangoRequest:
    def __init__(self, user_username, user_is_staff):
        self.user = MockDjangoUser(
            username=user_username,
            is_staff=user_is_staff
        )
