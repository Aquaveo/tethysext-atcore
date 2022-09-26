import os
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tethysext.atcore.utilities import parse_url
from tethysext.atcore.cli.cli_helpers import print_header, print_success, print_info, print_error

WORKSPACE = 'atcore'
RESOURCES = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
SLD_PATH = os.path.join(RESOURCES, 'sld_templates')


def init_atcore(arguments):
    """
    Commandline interface for initializing the atcore ext.
    """
    errors_occurred = False
    print_header('Initializing ATCORE...')

    if arguments.gsurl:
        gs_url = arguments.gsurl if arguments.gsurl.endswith('/') else f"{arguments.gsurl}/"
        url = parse_url(gs_url)
    else:
        url = parse_url("http://admin:geoserver@localhost:8181/geoserver/rest/")

    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint=url.endpoint,
        username=url.username,
        password=url.password
    )

    # Initialize workspace
    print_info('Initializing ATCORE GeoServer Workspace...')
    try:
        geoserver_engine.create_workspace(WORKSPACE, f'https://www.aquaveo.com/{WORKSPACE}')
        print_success('Successfully initialized ATCORE GeoServer workspace.')
    except Exception as e:
        errors_occurred = True
        print_error(f'An error occurred during workspace creation: {e}')

    # Initialize styles
    print_info('Initializing ATCORE GeoServer Styles...')
    sld_files = [f for f in os.listdir(SLD_PATH) if os.path.isfile(os.path.join(SLD_PATH, f)) and f.endswith('.sld')]
    for f in sld_files:
        try:
            geoserver_engine.create_style(
                style_id=f"{WORKSPACE}:{f.split('.')[0]}",
                sld_template=os.path.join(SLD_PATH, f),
                sld_context={},
                overwrite=True
            )
            print_success(f"Successfully initialized ATCORE GeoServer {f.split('.')[0]} style.")
        except Exception as e:
            errors_occurred = True
            print_error(f"An error occurred during {f.split('.')[0]} style creation: {e}")

    if not errors_occurred:
        print_success('Successfully initialized ATCORE.')
