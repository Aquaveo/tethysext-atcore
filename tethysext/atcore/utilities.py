"""
********************************************************************************
* Name: utilities
* Author: nswain
* Created On: July 30, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import re
from collections import namedtuple


Url = namedtuple('Url', ['protocol', 'username', 'password', 'host', 'port', 'path', 'endpoint'])


def parse_url(url):
    """
    Splits url into parts.
    e.g.: "http://admin:geoserver@localhost:8181/geoserver/rest"
    """
    url_pattern = r'(?P<protocol>[\w]*)://(?P<username>[\w\-\.]*):(?P<password>[\w\-\.!@#\$%&\*|]*)' \
                  r'@(?P<host>[\w\-\.]*):*(?P<port>[0-9]*)/(?P<path>[\w\-\./]*)'
    result = re.match(url_pattern, url)
    if result:
        if result.group('port'):
            endpoint = '{}://{}:{}/{}'.format(
                result.group('protocol'),
                result.group('host'),
                result.group('port'),
                result.group('path')
            )
        else:
            endpoint = '{}://{}/{}'.format(
                result.group('protocol'),
                result.group('host'),
                result.group('path')
            )
        return Url(
            protocol=result.group('protocol'),
            username=result.group('username'),
            password=result.group('password'),
            host=result.group('host'),
            port=result.group('port'),
            path=result.group('path'),
            endpoint=endpoint
        )
    else:
        raise ValueError('Invalid url given: {}'.format(url))
