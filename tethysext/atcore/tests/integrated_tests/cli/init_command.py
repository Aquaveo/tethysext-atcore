import os
import unittest
from unittest import mock

from tethysext.atcore.cli.init_command import init_atcore


class CLICommandTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.cli.init_command.os.path.isfile')
    @mock.patch('tethysext.atcore.cli.init_command.os.path.join')
    @mock.patch('tethysext.atcore.cli.init_command.os.listdir')
    @mock.patch('tethysext.atcore.cli.init_command.GeoServerAPI.create_style')
    @mock.patch('tethysext.atcore.cli.init_command.GeoServerSpatialDatasetEngine.create_workspace')
    def test_init_command(self, mock_workspace, mock_style, mock_listdir, mock_path, _):
        mock_listdir.return_value = ['dynamic_raster_style.sld']
        mock_path.return_value = '/path/to/dynamic_raster_style.sld'
        mock_args = mock.MagicMock(gsurl="http://admin:pass@example.com:8181/geoserver/rest/")

        with mock.patch('sys.stdout', open(os.devnull, 'w')):
            init_atcore(mock_args)

        mock_workspace.assert_called_once()
        mock_style.assert_called_with(
            workspace='atcore',
            style_name='dynamic_raster_style',
            sld_template='/path/to/dynamic_raster_style.sld',
            sld_context={},
            overwrite=True
        )

    @mock.patch('tethysext.atcore.cli.init_command.os.path.isfile')
    @mock.patch('tethysext.atcore.cli.init_command.print_error')
    @mock.patch('tethysext.atcore.cli.init_command.os.path.join')
    @mock.patch('tethysext.atcore.cli.init_command.os.listdir')
    @mock.patch('tethysext.atcore.cli.init_command.GeoServerAPI.create_style')
    @mock.patch('tethysext.atcore.cli.init_command.GeoServerSpatialDatasetEngine.create_workspace')
    def test_init_command_exceptions(self, mock_workspace, mock_style, mock_listdir, mock_path, mock_print, _):
        mock_listdir.return_value = ['dynamic_raster_style.sld']
        mock_path.return_value = '/path/to/dynamic_raster_style.sld'
        mock_args = mock.MagicMock(gsurl=False)

        mock_workspace.side_effect = [Exception('test exception')]
        mock_style.side_effect = [Exception('test exception')]

        with mock.patch('sys.stdout', open(os.devnull, 'w')):
            init_atcore(mock_args)

        self.assertEqual(mock_print.call_args_list[0][0][0],
                         'An error occurred during workspace creation: test exception')
        self.assertEqual(mock_print.call_args_list[1][0][0],
                         'An error occurred during dynamic_raster_style style creation: test exception')

    @mock.patch('tethysext.atcore.cli.init_command.print_success')
    @mock.patch('tethysext.atcore.cli.init_command.GeoServerAPI.create_style')
    @mock.patch('tethysext.atcore.cli.init_command.GeoServerSpatialDatasetEngine.create_workspace')
    def test_init_command_error(self, mock_workspace, mock_style, mock_print):
        mock_args = mock.MagicMock(gsurl=False)

        mock_workspace.side_effect = [Exception('test exception')]
        mock_style.side_effect = [Exception('test exception')]

        with mock.patch('sys.stdout', open(os.devnull, 'w')):
            init_atcore(mock_args)

        mock_print.assert_not_called()
