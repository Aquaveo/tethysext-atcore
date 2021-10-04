"""
********************************************************************************
* Name: utilities
* Author: nswain
* Created On: July 30, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import re
from collections import namedtuple
from contextlib import contextmanager

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


def generate_geoserver_urls(gs_engine):
    username = gs_engine.username
    password = gs_engine.password
    endpoint = gs_engine.endpoint
    public_endpoint = gs_engine.public_endpoint

    parts = endpoint.split('://')
    if len(parts) > 1:
        protocol = parts[0]
        endpoint_no_protocol = parts[1]
    else:
        protocol = ''
        endpoint_no_protocol = parts[0]

    public_parts = public_endpoint.split('://')
    if len(public_parts) > 1:
        public_protocol = public_parts[0]
        public_endpoint_no_protocol = public_parts[1]
    else:
        public_protocol = ''
        public_endpoint_no_protocol = public_parts[0]

    url = f'{protocol}://{username}:{password}@{endpoint_no_protocol}'
    public_url = f'{public_protocol}://{username}:{password}@{public_endpoint_no_protocol}'

    return url, public_url


def clean_request(request):
    """
    Strip the "method" variable from the GET and POST params of a request.

    Args:
        request(HttpRequest): the request.

    Returns:
        HttpRequest: the modified request
    """
    # Save mutability of GET and POST
    get_mutable = request.GET._mutable
    post_mutable = request.POST._mutable

    # Make GET and POST mutable
    request.GET._mutable = True
    request.POST._mutable = True

    # Pop off the 'method' parameter
    request.GET.pop('method', None)
    request.POST.pop('method', None)

    # Restore mutability
    request.GET._mutable = get_mutable
    request.POST._mutable = post_mutable

    return request


def strip_list(the_list, *args):
    """
    Strip emtpy items from end of list.

    Args:
        the_list(list): the list.
        *args: any number of values to strip from the end of the list.
    """
    targets = ''

    if args:
        targets = args

    while True:
        if len(the_list) == 0:
            break

        back = the_list[-1]

        if back not in targets:
            break

        the_list.pop(-1)

    return the_list


def grammatically_correct_join(strings, conjunction="and"):
    join_strings = ', '.join(strings[:-2] + [f" {conjunction} ".join(strings[-2:])])
    return join_strings


def import_from_string(path):
    """
    Import object from given dot-path string.

    Args:
        path<str>: Dot-path to Class, Function or other object in a module (e.g. foo.bar.Klass).
    """
    # Split into parts and extract function name
    module_path, obj_name = path.rsplit('.', 1)

    # Import module
    module = __import__(module_path, fromlist=[str(obj_name)])

    # Import the function or class
    obj = getattr(module, obj_name)
    return obj


@contextmanager
def temp_umask(new_umask):
    curr_umask = os.umask(new_umask)
    yield
    os.umask(curr_umask)