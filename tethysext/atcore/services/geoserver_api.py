"""
********************************************************************************
* Name: gs_api.py
* Author: nswain
* Created On: April 28, 2016
* Copyright: (c) Aquaveo 2016
* License:
********************************************************************************
"""
import logging
import os
import shutil
import tempfile
from zipfile import is_zipfile, ZipFile

import requests
from jinja2 import Template

log = logging.getLogger('atcore.geoserver-api')


class GeoServerAPI(object):
    """
    Custom interface for GeoServer
    """
    XML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'xml_templates')
    WARNING_STATUS_CODES = [403, 404]
    GEOSERVER_CLUSTER_PORTS = (8082, 8083, 8084)

    GWC_OP_SEED = 'seed'
    GWC_OP_RESEED = 'reseed'
    GWC_OP_TRUNCATE = 'truncate'
    GWC_OP_MASS_TRUNCATE = 'masstruncate'
    GWC_OPERATIONS = (GWC_OP_SEED, GWC_OP_RESEED, GWC_OP_TRUNCATE, GWC_OP_MASS_TRUNCATE)

    GWC_KILL_ALL = 'all'
    GWC_KILL_RUNNING = 'running'
    GWC_KILL_PENDING = 'pending'
    GWC_KILL_OPERATIONS = (GWC_KILL_ALL, GWC_KILL_PENDING, GWC_KILL_RUNNING)

    GWC_STATUS_ABORTED = -1
    GWC_STATUS_PENDING = 0
    GWC_STATUS_RUNNING = 1
    GWC_STATUS_DONE = 2
    GWC_STATUS_MAP = {
        GWC_STATUS_ABORTED: 'Aborted',
        GWC_STATUS_PENDING: 'Pending',
        GWC_STATUS_RUNNING: 'Running',
        GWC_STATUS_DONE: 'Done'
    }

    CT_AIG = 'AIG'
    CT_ARC_GRID = 'ArcGrid'
    CT_DTED = 'DTED'
    CT_ECW = 'ECW'
    CT_EHDR = 'EHdr'
    CT_ENVIHDR = 'ENVIHdr'
    CT_ERDASIMG = 'ERDASImg'
    CT_GEOTIFF = 'GeoTIFF'
    CT_GRASS_GRID = 'GrassGrid'
    CT_GTOPO30 = 'Gtopo30'
    CT_IMAGE_MOSAIC = 'ImageMosaic'
    CT_IMAGE_PYRAMID = 'ImagePyramid'
    CT_JP2MRSID = 'JP2MrSID'
    CT_MRSID = 'MrSID'
    CT_NETCDF = 'NetCDF'
    CT_NITF = 'NITF'
    CT_RPFTOC = 'RPFTOC'
    CT_RST = 'RST'
    CT_WORLD_IMAGE = 'WorldImage'

    VALID_COVERAGE_TYPES = (CT_AIG, CT_ARC_GRID, CT_DTED, CT_ECW, CT_EHDR, CT_ENVIHDR, CT_ERDASIMG, CT_GEOTIFF,
                            CT_GRASS_GRID, CT_GTOPO30, CT_IMAGE_MOSAIC, CT_IMAGE_PYRAMID, CT_JP2MRSID, CT_MRSID,
                            CT_NETCDF, CT_NITF, CT_RPFTOC, CT_RST, CT_WORLD_IMAGE)

    def __init__(self, gs_engine):
        """
        Constructor
        """
        self.gs_engine = gs_engine

    def get_ows_endpoint(self, workspace, public_endpoint=True):
        """
        Returns the GeoServer endpoint for OWS services (with trailing slash).

        Args:
            workspace (str): the name of the workspace
            public_endpoint (bool): return with the public endpoint if True.
        """
        gs_endpoint = self.gs_engine.public_endpoint if public_endpoint else self.gs_engine.endpoint
        gs_endpoint = gs_endpoint.replace('rest', '{0}/ows'.format(workspace))

        # Add trailing slash for consistency.
        if gs_endpoint[-1] != '/':
            gs_endpoint += '/'
        return gs_endpoint

    def get_wms_endpoint(self, public=True):
        """
        Returns the GeoServer endpoint for WMS services (with trailing slash).

        Args:
            public (bool): return with the public endpoint if True.
        """
        gs_endpoint = self.gs_engine.public_endpoint if public else self.gs_engine.endpoint
        gs_endpoint = gs_endpoint.replace('rest', 'wms')

        # Add trailing slash for consistency.
        if gs_endpoint[-1] != '/':
            gs_endpoint += '/'
        return gs_endpoint

    def get_gwc_endpoint(self, public_endpoint=True):
        """
        Returns the GeoServer endpoint for GWC services (with trailing slash).

        Args:
            public_endpoint (bool): return with the public endpoint if True.
        """
        gs_endpoint = self.gs_engine.public_endpoint if public_endpoint else self.gs_engine.endpoint
        gs_endpoint = gs_endpoint.replace('rest', 'gwc')

        # Add trailing slash for consistency.
        if gs_endpoint[-1] != '/':
            gs_endpoint += '/'

        gs_endpoint += 'rest/'
        return gs_endpoint

    def reload(self, ports=None, public_endpoint=True):
        """
        Reload the configuration from disk.

        Args:
            ports (iterable): A tuple or list of integers representing the ports on which different instances of
                              GeoServer are running in a clustered GeoServer configuration.
            public_endpoint (bool): Use the public geoserver endpoint if True, otherwise use the internal endpoint.
        """
        urls = []
        gs_endpoint = self.gs_engine.public_endpoint if public_endpoint else self.gs_engine.endpoint

        if ports is not None:
            gs_endpoint_template = gs_endpoint.replace('8181', '{0}')
            for port in ports:
                urls.append(gs_endpoint_template.format(port) + 'reload')
        else:
            urls.append(gs_endpoint + 'reload')

        log.debug("Catalog Reload URLS: {0}".format(urls))

        for url in urls:
            try:
                response = requests.post(url, auth=(self.gs_engine.username, self.gs_engine.password))

                if response.status_code != 200:
                    msg = "Catalog Reload Status Code {0}: {1}".format(response.status_code, response.text)
                    exception = requests.RequestException(msg, response=response)
                    log.error(exception)
            except requests.ConnectionError:
                log.warning('Catalog could not be reloaded on a GeoServer node.')

    def gwc_reload(self, ports=None, public_endpoint=True):
        """
                Reload the GeoWebCache configuration from disk.

                Args:
                    ports (iterable): A tuple or list of integers representing the ports on which different instances of
                                      GeoServer are running in a clustered GeoServer configuration.
                    public_endpoint (bool): Use the public geoserver endpoint if True, otherwise use the internal
                                            endpoint.
                """
        urls = []
        gwc_endpoint = self.get_gwc_endpoint(public_endpoint=public_endpoint)

        if ports is not None:
            gs_endpoint_template = gwc_endpoint.replace('8181', '{0}')
            for port in ports:
                urls.append(gs_endpoint_template.format(port) + 'reload')
        else:
            urls.append(gwc_endpoint + 'reload')

        log.debug("GeoWebCache Reload URLS: {0}".format(urls))

        for url in urls:
            retries_remaining = 3
            while retries_remaining > 0:
                try:
                    response = requests.post(url, auth=(self.gs_engine.username, self.gs_engine.password))

                    if response.status_code != 200:
                        msg = "GeoWebCache Reload Status Code {0}: {1}".format(response.status_code, response.text)
                        exception = requests.RequestException(msg, response=response)
                        log.error(exception)
                        retries_remaining -= 1
                        continue

                except requests.ConnectionError:
                    log.warning('GeoWebCache could not be reloaded on a GeoServer node.')
                    retries_remaining -= 1

                break

    def get_layer_extent(self, workspace, datastore_name, feature_name, native=False, buffer_factor=1.000001):
        """
        Get the legend extent for the given layer.

        Args:
            workspace: Name of the workspace to which all of the styles and layers belong or will belong to.
            datastore_name: Name of a PostGIS GeoServer data store (assumption: the datastore belongs to the workspace).
            feature_name: Name of the feature type. Will also be used to name the layer.
            native (bool): True if the native projection extent should be used. Defaults to False.
            buffer_factor(float): Apply a buffer around the bounding box.
        """

        url = (self.gs_engine.endpoint + 'workspaces/' + workspace + '/datastores/' + datastore_name
               + '/featuretypes/' + feature_name + '.json')

        response = requests.get(url, auth=(self.gs_engine.username, self.gs_engine.password))

        if response.status_code != 200:
            msg = "Get Layer Extent Status Code {0}: {1}".format(response.status_code, response.text)
            exception = requests.RequestException(msg, response=response)
            log.error(exception)
            raise exception

        # Get the JSON
        json = response.json()

        # Default bounding box
        bbox = None
        extent = [-128.583984375, 22.1874049914, -64.423828125, 52.1065051908]

        # Extract bounding box
        if 'featureType' in json:
            if native:
                if 'nativeBoundingBox' in json['featureType']:
                    bbox = json['featureType']['nativeBoundingBox']
            else:
                if 'latLonBoundingBox' in json['featureType']:
                    bbox = json['featureType']['latLonBoundingBox']

        if bbox is not None:
            # minx, miny, maxx, maxy
            extent = [bbox['minx'] / buffer_factor, bbox['miny'] / buffer_factor,
                      bbox['maxx'] * buffer_factor, bbox['maxy'] * buffer_factor]

        return extent

    def create_postgis_store(self, workspace, name, db_host, db_port, db_name, db_username, db_password,
                             max_connections=5, max_connection_idle_time=30, evictor_run_periodicity=30,
                             validate_connections=True):
        """
        Use this method to link an existing PostGIS database to GeoServer as a feature store. Note that this method only works for data in vector formats.

        Args:
          workspace (string): Workspace in which the store will be created. Note that the workspace must be an existing workspace. If no workspace is given, the default workspace will be assigned.
          name (string): Name of the store to which the new postgis resource will be added.
          db_host (string): Host of the PostGIS database (e.g.: 'www.example.com').
          db_port (string): Port of the PostGIS database (e.g.: '5432')
          db_name (string): Name of the database.
          db_username (string): Database user that has access to the database.
          db_password (string): Password of database user.
          max_connections (int, optional): Maximum number of connections allowed in connection pool. Defaults to 5.
          max_connection_idle_time (int, optional): Number of seconds a connections can stay idle before the evictor considers closing it. Defaults to 30 seconds.
          evictor_run_periodicity (int, optional): Number of seconds between idle connection evictor runs. Defaults to 30 seconds.
          validate_connections (bool, optional): Test connections before using. Defaults to False.

        Examples:

          engine.create_postgis_store(workspace='workspace', store_name='store_name', host='localhost', port='5432', database='database_name', user='user', password='pass')

        """  # noqa: E501
        # Create the store
        validate_connections_string = 'true' if validate_connections else 'false'

        xml = """
              <dataStore>
                <name>{0}</name>
                <connectionParameters>
                  <entry key="host">{1}</entry>
                  <entry key="port">{2}</entry>
                  <entry key="database">{3}</entry>
                  <entry key="user">{4}</entry>
                  <entry key="passwd">{5}</entry>
                  <entry key="dbtype">postgis</entry>
                  <entry key="max connections">{6}</entry>
                  <entry key="Max connection idle time">{7}</entry>
                  <entry key="Evictor run periodicity">{8}</entry>
                  <entry key="validate connections">{9}</entry>
                </connectionParameters>
              </dataStore>
              """.format(name, db_host, db_port, db_name, db_username, db_password,
                         max_connections, max_connection_idle_time, evictor_run_periodicity,
                         validate_connections_string)

        # Prepare headers
        headers = {
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }

        # Prepare URL to create store
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/datastores'

        # Execute: POST /workspaces/<ws>/datastores
        response = requests.post(
            url=url,
            data=xml,
            headers=headers,
            auth=(self.gs_engine.username, self.gs_engine.password)
        )

        # Return with error if this doesn't work
        if response.status_code != 201:
            msg = "Create Postgis Store Status Code {0}: {1}".format(response.status_code, response.text)
            exception = requests.RequestException(msg, response=response)
            log.error(exception)
            raise exception

    def create_coverage_store(self, workspace, name, coverage_type):
        """
        Create a new coverage store.

        Args:
            workspace (str): Workspace in which the store will be created. Note that the workspace must be an existing workspace. If no workspace is given, the default workspace will be assigned.
            name (str): Name of the coverage store create.
            coverage_type (str): Type of coverage store to create (e.g.: GeoServerAPI.CT_ARC_GRID, GeoServerAPI.CT_GEOTIFF, GeoServerAPI.CT_GRASS_GRID).
        """  # noqa: E501
        # Validate coverage type
        if coverage_type not in self.VALID_COVERAGE_TYPES:
            raise ValueError('"{0}" is not a valid coverage_type. Use either {1}'.format(
                coverage_type, ', '.join(self.VALID_COVERAGE_TYPES)))

        # Black magic for grass grid support
        if coverage_type == self.CT_GRASS_GRID:
            coverage_type = self.CT_ARC_GRID

        xml = """
              <coverageStore>
                  <name>{name}</name>
                  <type>{type}</type>
                  <enabled>true</enabled>
                  <workspace>
                      <name>{workspace}</name>
                  </workspace>
              </coverageStore>
              """.format(name=name, type=coverage_type, workspace=workspace)

        # Prepare headers
        headers = {
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }

        # Prepare URL to create store
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/coveragestores'

        # Execute: POST /workspaces/<ws>/coveragestores
        response = requests.post(
            url=url,
            data=xml,
            headers=headers,
            auth=(self.gs_engine.username, self.gs_engine.password)
        )

        # Return with error if this doesn't work
        if response.status_code != 201:
            msg = "Create Coverage Store Status Code {0}: {1}".format(response.status_code, response.text)
            exception = requests.RequestException(msg, response=response)
            log.error(exception)
            raise exception

    def update_layer_styles(self, workspace, layer_name, default_style, other_styles=None):
        """
        Update/add styles to existing layer.

        Args:
            layer_name (str): Name of the layer.
            default_style (str): Name of default style.
            other_styles (list<str>): Additional styles to add to layer.
        """
        context = {
            'workspace': workspace,
            'default_style': default_style,
            'other_styles': other_styles or [],
            'geoserver_rest_endpoint': self.gs_engine.endpoint
        }

        # Open layer template
        layer_path = os.path.join(self.XML_PATH, 'layer_template.xml')
        url = self.gs_engine.endpoint + 'layers/' + layer_name + '.xml'
        headers = {
            "Content-type": "text/xml"
        }

        with open(layer_path, 'r') as layer_file:
            text = layer_file.read()
            template = Template(text)
            xml = template.render(context)

        retries_remaining = 3
        while retries_remaining > 0:
            response = requests.put(
                url,
                headers=headers,
                auth=(self.gs_engine.username, self.gs_engine.password),
                data=xml,
            )

            # Raise an exception if status code is not what we expect
            if response.status_code == 200:
                log.info('Successfully created layer {}'.format(layer_name))
                break
            else:
                retries_remaining -= 1
                if retries_remaining == 0:
                    msg = "Create Layer Status Code {0}: {1}".format(response.status_code, response.text)
                    exception = requests.RequestException(msg, response=response)
                    log.error(exception)
                    raise exception

    def create_layer(self, workspace, datastore_name, feature_name, geometry_type, srid, sql, default_style,
                     geometry_name='geometry', other_styles=None, parameters=None):
        """
        Direct call to GeoServer REST API to create SQL View feature types and layers.

        Args:
            workspace: Name of the workspace to which all of the styles and layers belong or will belong to.
            datastore_name: Name of a PostGIS GeoServer data store (assumption: the datastore belongs to the workspace).
            feature_name: Name of the feature type. Will also be used to name the layer.
            geometry_name: Name of the PostGIS column/field of type geom.
            geometry_type: Type of geometry in geometry field (e.g.: Point, LineString)
            srid (int): EPSG spatial reference id. EPSG spatial reference ID.
            sql: The SQL query that defines the feature type.
            default_style: The name of the default style (note: it is assumed this style belongs to the workspace).
            other_styles: A list of other default style names (assumption: these styles belong to the workspace).
            parameters: A list of parameter dictionaries { name, default_value, regex_validator }.
        """
        # Template context
        context = {
            'workspace': workspace,
            'datastore_name': datastore_name,
            'feature_name': feature_name,
            'geoserver_rest_endpoint': self.gs_engine.endpoint,
            'sql': sql,
            'geometry_name': geometry_name,
            'geometry_type': geometry_type,
            'srid': srid,
            'parameters': parameters or [],
            'default_style': default_style,
            'other_styles': other_styles or []
        }

        # Open sql view template
        sql_view_path = os.path.join(self.XML_PATH, 'sql_view_template.xml')
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/datastores/' + datastore_name + '/featuretypes'
        headers = {
            "Content-type": "text/xml"
        }
        with open(sql_view_path, 'r') as sql_view_file:
            text = sql_view_file.read()
            template = Template(text)
            xml = template.render(context)

        retries_remaining = 3
        while retries_remaining > 0:
            response = requests.post(
                url,
                headers=headers,
                auth=(self.gs_engine.username, self.gs_engine.password),
                data=xml,
            )

            # Raise an exception if status code is not what we expect
            if response.status_code == 201:
                log.info('Successfully created featuretype {}'.format(feature_name))
                break
            if response.status_code == 500 and 'already exists' in response.text:
                break
            else:
                retries_remaining -= 1
                if retries_remaining == 0:
                    msg = "Create Feature Type Status Code {0}: {1}".format(response.status_code, response.text)
                    exception = requests.RequestException(msg, response=response)
                    log.error(exception)
                    raise exception

        # Add styles to new layer
        self.update_layer_styles(
            workspace=workspace,
            layer_name=feature_name,
            default_style=default_style,
            other_styles=other_styles
        )

        # GeoWebCache Settings
        gwc_layer_path = os.path.join(self.XML_PATH, 'gwc_layer_template.xml')
        url = self.get_gwc_endpoint(public_endpoint=False) + 'layers/' + workspace + ':' + feature_name + '.xml'
        headers = {
            "Content-type": "text/xml"
        }
        with open(gwc_layer_path, 'r') as gwc_layer_file:
            text = gwc_layer_file.read()
            template = Template(text)
            xml = template.render(context)

        retries_remaining = 300
        while retries_remaining > 0:
            response = requests.put(
                url,
                headers=headers,
                auth=(self.gs_engine.username, self.gs_engine.password),
                data=xml,
            )

            if response.status_code == 200:
                log.info('Successfully created GeoWebCache layer {}'.format(feature_name))
                break
            else:
                log.warning("GWC DID NOT RETURN 200, but instead: {}. {}\n".format(response.status_code, response.text))
                retries_remaining -= 1
                if retries_remaining == 0:
                    msg = "Create GWC Layer Status Code {0}: {1}".format(response.status_code, response.text)
                    exception = requests.RequestException(msg, response=response)
                    log.error(exception)
                    raise exception

    def create_coverage_layer(self, workspace, coverage_name, coverage_type, coverage_file, default_style='',
                              other_styles=None):
        """
        Create a coverage store, coverage resource, and layer in the given workspace.

        Args:
            workspace (str): Name of the workspace to which all of the styles and layers belong or will belong to.
            coverage_name (str): Name of the coverage and coverage store that will be created.
            coverage_type (str): Type of coverage store to create (e.g.: GeoServerAPI.CT_ARC_GRID, GeoServerAPI.CT_GEOTIFF, GeoServerAPI.CT_GRASS_GRID).
            coverage_file (str): Path to coverage file or zip archive containing coverage file.
            default_style (str): The name of the default style (note: it is assumed this style belongs to the workspace).
            other_styles (list): A list of other default style names (assumption: these styles belong to the workspace).
        """  # noqa: E501
        # Validate coverage type
        if coverage_type not in self.VALID_COVERAGE_TYPES:
            exception = ValueError('"{0}" is not a valid coverage_type. Use either {1}'.format(
                coverage_type, ', '.join(self.VALID_COVERAGE_TYPES)))
            log.error(exception)
            raise exception

        # Only one coverage per coverage store, so we name coverage store the same as the coverage
        coverage_store_name = coverage_name

        # Prepare files
        working_dir = tempfile.mkdtemp()

        # Unzip to working directory if zip file
        if is_zipfile(coverage_file):
            zip_file = ZipFile(coverage_file)
            zip_file.extractall(working_dir)
        # Otherwise, copy to working directory
        else:
            shutil.copy2(coverage_file, working_dir)

        # Convert GrassGrids to ArcGrids
        if coverage_type == self.CT_GRASS_GRID:
            working_dir_contents = os.listdir(working_dir)
            num_working_dir_items = len(working_dir_contents)
            if num_working_dir_items > 2:
                exception = ValueError('Expected 1 or 2 files for coverage type "{}" but got {} instead: "{}"'.format(
                    self.CT_GRASS_GRID,
                    num_working_dir_items,
                    '", "'.join(working_dir_contents)
                ))
                log.error(exception)
                raise exception

            for item in working_dir_contents:
                # Skip directories
                if os.path.isdir(os.path.join(working_dir, item)):
                    continue

                # Skip the projection file
                if 'prj' in item:
                    continue

                # Assume other file is the raster
                corrupt_file = False
                tmp_coverage_path = os.path.join(working_dir, item)

                with open(tmp_coverage_path, 'r') as item:
                    contents = item.readlines()

                for line in contents[0:6]:
                    if 'north' in line:
                        north = float(line.split(':')[1].strip())
                    elif 'south' in line:
                        south = float(line.split(':')[1].strip())
                    elif 'east' in line:
                        pass  # we don't use east in this algorithm so skip it.
                    elif 'west' in line:
                        west = float(line.split(':')[1].strip())
                    elif 'rows' in line:
                        rows = int(line.split(':')[1].strip())
                    elif 'cols' in line:
                        cols = int(line.split(':')[1].strip())
                    else:
                        corrupt_file = True

                if corrupt_file:
                    exception = IOError('GRASS file could not be processed, check to ensure the GRASS grid is '
                                        'correctly formatted or included.')
                    log.error(exception)
                    raise exception

                # Calculate new header
                xllcorner = west
                yllcorner = south
                cellsize = (north - south) / rows

                header = ['ncols         {0}\n'.format(cols),
                          'nrows         {0}\n'.format(rows),
                          'xllcorner     {0}\n'.format(xllcorner),
                          'yllcorner     {0}\n'.format(yllcorner),
                          'cellsize      {0}\n'.format(cellsize)]

                # Strip off old header and add new one
                for _ in range(0, 6):
                    contents.pop(0)
                contents = header + contents

                # Write the coverage to file
                with open(tmp_coverage_path, 'w') as o:
                    for line in contents:
                        # Make sure the file ends with a new line
                        if line[-1] != '\n':
                            line = line + '\n'

                        o.write(line)

        # Prepare Files
        coverage_archive_name = coverage_name + '.zip'
        coverage_archive = os.path.join(working_dir, coverage_archive_name)
        with ZipFile(coverage_archive, 'w') as zf:
            for item in os.listdir(working_dir):
                if item != coverage_archive_name:
                    zf.write(os.path.join(working_dir, item), item)

        with open(coverage_archive, 'rb') as file_:
            files = {'file': file_}
            content_type = 'application/zip'

            # Prepare headers
            headers = {
                "Content-type": content_type,
                "Accept": "application/xml"
            }

            # Prepare URL
            extension = coverage_type.lower()

            if coverage_type == self.CT_GRASS_GRID:
                extension = self.CT_ARC_GRID.lower()

            url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/coveragestores/' + \
                coverage_store_name + '/file.' + extension

            # Set params
            params = {'coverageName': coverage_name}

            retries_remaining = 3
            zip_error_retries = 5
            raise_error = False

            while True:
                if coverage_type == self.CT_IMAGE_MOSAIC:
                    # Image mosaic doesn't need params argument.
                    response = requests.put(
                        url=url,
                        files=files,
                        headers=headers,
                        auth=(self.gs_engine.username, self.gs_engine.password)
                    )
                else:
                    response = requests.put(
                        url=url,
                        files=files,
                        headers=headers,
                        params=params,
                        auth=(self.gs_engine.username, self.gs_engine.password)
                    )

                # Raise an exception if status code is not what we expect
                if response.status_code == 201:
                    log.info('Successfully created coverage {}'.format(coverage_name))
                    break
                if response.status_code == 500 and 'already exists' in response.text:
                    log.warning('Coverage already exists {}'.format(coverage_name))
                    break
                if response.status_code == 500 and 'Error occured unzipping file' in response.text:
                    zip_error_retries -= 1
                    if zip_error_retries == 0:
                        raise_error = True
                else:
                    retries_remaining -= 1
                    if retries_remaining == 0:
                        raise_error = True

                if raise_error:
                    msg = "Create Coverage Status Code {0}: {1}".format(response.status_code, response.text)
                    exception = requests.RequestException(msg, response=response)
                    log.error(exception)
                    raise exception

        if working_dir:
            shutil.rmtree(working_dir)

        # Add styles to new layer
        self.update_layer_styles(
            workspace=workspace,
            layer_name=coverage_name,
            default_style=default_style,
            other_styles=other_styles
        )

    def create_layer_group(self, workspace, group_name, layer_names, default_styles):
        context = {
            'name': group_name,
            'layers': layer_names,
            'styles': default_styles
        }

        # Open layer group template
        template_path = os.path.join(self.XML_PATH, 'layer_group_template.xml')
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/layergroups.json'
        headers = {
            "Content-type": "text/xml"
        }

        with open(template_path, 'r') as template_file:
            text = template_file.read()
            template = Template(text)
            xml = template.render(context)

        response = requests.post(
            url,
            headers=headers,
            auth=(self.gs_engine.username, self.gs_engine.password),
            data=xml,
        )

        if response.status_code != 201:
            msg = "Create Layer Group Status Code {}: {}".format(response.status_code, response.text)
            exception = requests.RequestException(msg, response=response)
            log.error(exception)
            raise exception

    def create_style(self, workspace, style_name, sld_template, sld_context=None, overwrite=False):
        """
        Create style layer from and SLD template.

        Args
          workspace: the name of the workspace to add the style to
          style_name: the name of the style to create
          sld_template: path to SLD template file.
          sld_context: a dictionary with context variables to be rendered in the template.
          overwrite (bool, optional): Will overwrite existing style with same name if True. Defaults to False.
        """
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/styles'

        if overwrite:
            try:
                self.delete_style(workspace=workspace, style_name=style_name, purge=True)
            except Exception as e:
                if 'referenced by existing' in str(e):
                    log.error(str(e))
                    raise

        # Use post request to create style container first
        headers = {'Content-type': 'application/vnd.ogc.sld+xml'}

        # Render the SLD template
        with open(sld_template, 'r') as sld_file:
            text = sld_file.read()

        if sld_context is not None:
            template = Template(text)
            text = template.render(sld_context)

        response = requests.post(
            url,
            headers=headers,
            auth=(self.gs_engine.username, self.gs_engine.password),
            params={'name': style_name},
            data=text
        )

        # Raise an exception if status code is not what we expect
        if response.status_code == 201:
            log.info('Successfully created style {}'.format(style_name))
        else:
            msg = 'Create Style Status Code {0}: {1}'.format(response.status_code, response.text)
            if response.status_code == 500:
                if 'Unable to find style for event' in response.text or 'Error persisting' in response.text:
                    log.warning('Created style {} with warnings: {}'.format(style_name, response.text))
                else:
                    exception = requests.RequestException(msg, response=response)
                    log.error(msg)
                    raise exception
            else:
                exception = requests.RequestException(msg, response=response)
                log.error(msg)
                raise exception

    def delete_coverage_store(self, workspace, name, recurse=True, purge=True):
        """
        Delete the specified coverage store.
        Args:
            workspace (str): the name of the workspace to add the style to
            name(str):name of the coverage
            recurse (bool): recursively delete any dependent objects if True.
            purge (bool): delete configuration files from filesystem if True. remove file from disk of geoserver.

        Returns:

        """
        # Prepare headers
        headers = {
            "Content-type": "application/json"
        }

        # Prepare URL to create store
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/coveragestores/' + name

        json = {'recurse': recurse,
                'purge': purge}

        # Execute: POST /workspaces/<ws>/coveragestores/<cs>
        response = requests.delete(
            url=url,
            headers=headers,
            params=json,
            auth=(self.gs_engine.username, self.gs_engine.password)
        )

        if response.status_code != 200:
            if response.status_code in self.WARNING_STATUS_CODES:
                msg = "Delete Coverage Store Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.warning(exception)
            else:
                msg = "Delete Coverage Store Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.error(exception)
                raise exception

    def delete_layer(self, workspace, datastore, name, recurse=False):
        """
        Args:
            workspace: Name of workspace
            datastore: Name of datastore
            name: name of features
            recurse (bool): recursively delete any dependent objects if True.
        """
        featuretype_url = '{0}workspaces/{1}/datastores/{2}/featuretypes/{3}'.format(self.gs_engine.endpoint,
                                                                                     workspace,
                                                                                     datastore,
                                                                                     name)
        # Prepare delete request
        headers = {
            "Content-type": "application/json"
        }

        json = {'recurse': recurse}

        response = requests.delete(
            featuretype_url,
            auth=(self.gs_engine.username, self.gs_engine.password),
            headers=headers,
            params=json
        )

        # Raise an exception if status code is not what we expect
        if response.status_code != 200:
            if response.status_code in self.WARNING_STATUS_CODES:
                msg = "Delete Layer Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.warning(exception)
            else:
                msg = "Delete Layer Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.error(exception)
                raise exception

    def delete_layer_group(self, workspace, group_name):
        """
        Args:
            workspace: Name of workspace
            group_name: name of layer group
        """
        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/layergroups/{0}'.format(group_name)
        response = requests.delete(url, auth=(self.gs_engine.username, self.gs_engine.password))
        if response.status_code != 200:
            if response.status_code == 404 and "No such layer group" in response.text:
                return
            else:
                msg = "Delete Layer Group Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.error(exception)
                raise exception

    def delete_style(self, workspace, style_name, purge=False):
        """
        Delete the style with the given workspace and style name.

        Args:
            workspace: name of the workspace the style belongs to.
            style_name: name of the style to delete.
            purge (bool): delete configuration files from filesystem if True. remove file from disk of geoserver.

        Returns:
        """

        url = self.gs_engine.endpoint + 'workspaces/' + workspace + '/styles/' + style_name

        # Prepare delete request
        headers = {
            "Content-type": "application/json"
        }

        json = {'purge': purge}

        response = requests.delete(
            url,
            auth=(self.gs_engine.username, self.gs_engine.password),
            headers=headers,
            params=json
        )

        # Raise an exception if status code is not what we expect
        if response.status_code != 200:
            if response.status_code in self.WARNING_STATUS_CODES:
                msg = "Delete Style Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.warning(exception)
            else:
                msg = "Delete Style Status Code {0}: {1}".format(response.status_code, response.text)
                exception = requests.RequestException(msg, response=response)
                log.error(exception)
                raise exception

    def modify_tile_cache(self, workspace, name, operation, zoom_start=10, zoom_end=15, grid_set_id=900913,
                          image_format='image/png', thread_count=1, bounds=None, parameters=None):
        """
        Modify all or a portion of the GWC tile cache for given layer. Operations include seed, reseed, and truncate.

        Args:
            workspace (str): name of the workspace the style belongs to.
            name (str): name of the layer on which to perform tile cache operation.
            operation (str): operation type either 'seed', 'reseed', 'truncate', or 'masstruncate'.
            zoom_start (int, optional): beginning of zoom range on which to perform tile cache operation. Minimum is 0. Defaults to 10.
            zoom_end (int, optional): end of zoom range on which to perform tile cache operation. It is not usually recommended to seed past zoom 20. Maximum is 30. Defaults to 15.
            grid_set_id (int, optional): ID of the grid set on which to perform the tile cache operation. Either 4326 for Geographic or 900913 for Web Mercator. Defaults to 900913.
            image_format (str, optional): format of tiles on which to perform tile cache operation. Defaults to 'image/png'.
            thread_count (int, optional): number of threads to used to perform tile cache operation. Defaults to 1.
            bounds (list, optional): list with ordinates of bounding box of area on which to perform tile cache operation (e.g.: [minx, miny, maxx, maxy]).
            parameters (dict, optional): Key value pairs of parameters to use to filter tile cache operation.

        Raises:
            requests.RequestException: if modify tile cache operation is not submitted successfully.
            ValueError: if invalid value is provided for an argument.
        """  # noqa: E501
        if operation not in self.GWC_OPERATIONS:
            raise ValueError('Invalid value "{}" provided for argument "operation". Must be "{}".'.format(
                operation, '" or "'.join(self.GWC_OPERATIONS))
            )

        # Use post request to create style container first
        headers = {'Content-type': 'text/xml'}

        if operation == self.GWC_OP_MASS_TRUNCATE:
            url = self.get_gwc_endpoint() + 'masstruncate/'
            xml_text = '<truncateLayer><layerName>{}:{}</layerName></truncateLayer>'.format(workspace, name)

            response = requests.post(
                url,
                headers=headers,
                auth=(self.gs_engine.username, self.gs_engine.password),
                data=xml_text
            )

        else:
            url = self.get_gwc_endpoint() + 'seed/' + workspace + ':' + name + '.xml'
            xml = os.path.join(self.XML_PATH, 'gwc_tile_cache_operation_template.xml')

            # Open XML file
            with open(xml, 'r') as sld_file:
                text = sld_file.read()

            # Compose XML context
            xml_context = {
                'workspace': workspace,
                'name': name,
                'operation': operation,
                'grid_set_id': grid_set_id,
                'zoom_start': zoom_start,
                'zoom_end': zoom_end,
                'format': image_format,
                'thread_count': thread_count,
                'parameters': parameters,
                'bounds': bounds
            }

            # Render the XML template
            template = Template(text)
            rendered = template.render(xml_context)

            response = requests.post(
                url,
                headers=headers,
                auth=(self.gs_engine.username, self.gs_engine.password),
                data=rendered
            )

        # Raise an exception if status code is not what we expect
        if response.status_code == 200:
            log.info('Successfully submitted {} tile cache operation for layer {}:{}'.format(
                operation, workspace, name
            ))
        else:
            msg = 'Unable to submit {} tile cache operation for layer {}:{}. {}:{}'.format(
                operation, workspace, name, response.status_code, response.text
            )
            exception = requests.RequestException(msg, response=response)
            log.error(msg)
            raise exception

    def terminate_tile_cache_tasks(self, workspace, name, kill='all'):
        """
        Terminate running tile cache processes for given layer.

        Args:
            workspace (str): name of the workspace the style belongs to.
            name (str): name of the layer on which to terminate tile cache operations.
            kill (str): specify which type of task to terminate. Either 'running', 'pending', or 'all'.

        Raises:
            requests.RequestException: if terminate tile cache operation cannot be submitted successfully.
            ValueError: if invalid value is provided for an argument.
        """
        if kill not in self.GWC_KILL_OPERATIONS:
            raise ValueError('Invalid value "{}" provided for argument "kill". Must be "{}".'.format(
                kill, '" or "'.join(self.GWC_KILL_OPERATIONS))
            )

        url = self.get_gwc_endpoint() + 'seed/' + workspace + ':' + name

        response = requests.post(
            url,
            auth=(self.gs_engine.username, self.gs_engine.password),
            data={'kill_all': kill}
        )

        if response.status_code != 200:
            msg = 'Unable to query tile cache status for layer {}:{}. {}:{}'.format(
                workspace, name, response.status_code, response.text
            )
            exception = requests.RequestException(msg, response=response)
            raise exception

    def query_tile_cache_tasks(self, workspace, name):
        """
        Get the status of running tile cache tasks for a layer.

        Args:
            workspace (str): name of the workspace the style belongs to.
            name (str): name of the layer on which to get status.

        Returns:
            list: list of dictionaries with status with keys: 'tiles_processed', 'total_to_process', 'num_remaining', 'task_id', 'task_status'

        Raises:
            requests.RequestException: if query tile cache operation cannot be submitted successfully.
        """  # noqa: E501
        url = self.get_gwc_endpoint() + 'seed/' + workspace + ':' + name + '.json'
        status_list = []

        response = requests.get(
            url,
            auth=(self.gs_engine.username, self.gs_engine.password),
        )

        if response.status_code == 200:
            status = response.json()

            if 'long-array-array' in status:
                for s in status['long-array-array']:
                    temp_dict = {
                        'tiles_processed': s[0],
                        'total_to_process': s[1],
                        'num_remaining': s[2],
                        'task_id': s[3],
                        'task_status': self.GWC_STATUS_MAP[s[4]] if s[4] in self.GWC_STATUS_MAP else s[4]
                    }

                    status_list.append(dict(temp_dict))
            return status_list
        else:
            msg = 'Unable to terminate tile cache tasks for layer {}:{}. {}:{}'.format(
                workspace, name, response.status_code, response.text
            )
            exception = requests.RequestException(msg, response=response)
            raise exception

    def enable_time_dimension(self, workspace, coverage_name):
        """
        Enable time dimension for a given image mosaic layer

        Args:
            workspace (str): name of the workspace the style belongs to.
            coverage_name (str): name of the image mosaic layer.

        Raises:
            requests.RequestException: if enable time dimension operation cannot be executed successfully.
        """
        headers = {
            "Content-type": "text/xml"
        }
        url = f"{self.gs_engine.endpoint}workspaces/{workspace}/coveragestores/{coverage_name}" \
              f"/coverages/{coverage_name}"
        data_xml = '<coverage>\
                    <enabled>true</enabled>\
                    <metadata><entry key="time">\
                    <dimensionInfo>\
                    <enabled>true</enabled>\
                    <presentation>LIST</presentation>\
                    <units>ISO8601</units><defaultValue/>\
                    </dimensionInfo>\
                    </entry></metadata>\
                    </coverage>'
        response = requests.put(
            url,
            headers=headers,
            auth=(self.gs_engine.username, self.gs_engine.password),
            data=data_xml,
        )

        if response.status_code != 200:
            msg = f"Enable Time Dimension Layer {coverage_name} with Status Code {response.status_code}:" \
                  f" {response.text}"
            exception = requests.RequestException(msg, response=response)
            log.error(exception)
            raise exception
