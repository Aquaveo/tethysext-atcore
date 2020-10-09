"""
********************************************************************************
* Name: __init__.py
* Author: Michael Souffront and Tran Hoang
* Created On: Oct 9, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import argparse
from tethysext.atcore.cli.init_command import init_atcore


def atcore_command():
    """
    atcore commandline interface function.
    """
    # Create parsers
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Commands')

    # init command ----------------------------------------------------------------------------------------------------#
    init_parser = subparsers.add_parser(
        'init',
        help="Initialize the atcore extension."
             "(e.g.: 'atcore init' or 'atcore init --gsurl http://admin:geoserver@localhost:8181/geoserver/rest/')."
    )
    init_parser.add_argument(
        '--gsurl',
        nargs='?',
        help='GeoServer url to geoserver rest endpoint '
             '(e.g.: "http://admin:geoserver@localhost:8181/geoserver/rest/").'
    )
    init_parser.set_defaults(func=init_atcore)

    # Parse commandline arguments and call command --------------------------------------------------------------------#
    args = parser.parse_args()
    args.func(args)
