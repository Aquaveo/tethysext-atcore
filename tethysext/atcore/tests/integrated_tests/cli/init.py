import unittest
from unittest import mock

from tethysext.atcore.cli import atcore_command


class AtcoreCommandTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.cli.argparse.ArgumentParser.parse_args')
    @mock.patch('tethysext.atcore.cli.argparse.ArgumentParser.add_argument')
    def test_atcore_command(self, mock_add_arguments, _):
        atcore_command()

        mock_add_arguments.assert_called_with(
            '--gsurl',
            nargs='?',
            help='GeoServer url to geoserver rest endpoint '
                 '(e.g.: "http://admin:geoserver@localhost:8181/geoserver/rest/").'
        )
