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


def clean_request(request):
    """
    Strip the "method" variable from the GET and POST params of a request.

    Args:
        request(HttpRequest): the request.

    Returns:
        HttpRequest: the modified request
    """
    # Save mutablility of GET and POST
    get_mutable = request.GET._mutable
    post_mutable = request.POST._mutable

    # Make GET and POST mutable
    request.GET._mutable = True
    request.POST._mutable = True

    # Pop off the 'method' parameter
    request.GET.pop('method', None)
    request.POST.pop('method', None)

    # Restore mutabilility
    request.GET._mutable = get_mutable
    request.POST._mutable = post_mutable

    return request


def strip_list(l, *args):
    """
    Strip emtpy items from end of list.

    Args:
        l(list): the list.
        *args: any number of values to strip from the end of the list.
    """
    targets = ''

    if args:
        targets = args

    while True:
        if len(l) == 0:
            break

        back = l[-1]

        if back not in targets:
            break

        l.pop(-1)

    return l
