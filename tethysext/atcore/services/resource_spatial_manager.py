"""
********************************************************************************
* Name: model_db_spatial_manager
* Author: nswain
* Created On: July 06, 2018
* Updated on: December 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
from jinja2 import Template

from abc import abstractmethod

from tethysext.atcore.services.exceptions import UnitsNotFound, UnknownUnits
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager

from tethysext.atcore.services.base_spatial_manager import reload_config

class ResourceSpatialManager(BaseSpatialManager):
    """
    Class for Spatial Managers using a postgres database.
    """

    SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sql_templates')
    SLD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sld_templates')

    # Vector Layer Types
    VL_EXTENT_VIEW = 'resource_extent_layer_view'
    VL_EXTENT_TEMPLATE = 'resource_extent_layer_style'

    @abstractmethod
    def get_extent_for_project(self, model_db):
        """
        Return the extent / bounding box for a project/model.
        Args:
            model_db (ModelDatabase): the object representing the model database.
        Returns:
            4-list: Extent bounding box (e.g.: [minx, miny, maxx, maxy] ).
        """

    def get_projection_units(self, model_db, srid):
        """
        Get units of the given projection.

        Args:
            model_db(ModelDatabase): the object representing the model database.:
            srid(int): EPSG spatial reference identifier.

        Returns:
            str: SpatialManager.U_METRIC or SpatialManager.U_IMPERIAL
        """
        if srid not in self._projection_units:
            db_engine = model_db.get_engine()
            try:
                sql = "SELECT srid, proj4text FROM spatial_ref_sys WHERE srid = {}".format(srid)
                ret = db_engine.execute(sql)

                # Parse proj4text to get units
                # e.g.: +proj=utm +zone=21 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs
                proj4text = ''
                units = ''

                for row in ret:
                    proj4text = row.proj4text
            finally:
                db_engine.dispose()

            proj4parts = proj4text.split('+')

            for part in proj4parts:
                spart = part.strip()
                if 'units' in spart:
                    units = spart.replace('units=', '')

            if not units:
                raise UnitsNotFound('Unable to determine units of project with srid: {}'.format(srid))

            if 'ft' in units:
                self._projection_units[srid] = self.U_IMPERIAL
            elif 'm' in units:
                self._projection_units[srid] = self.U_METRIC
            else:
                raise UnknownUnits('"{}" is an unrecognized form of units. From srid: {}'.format(units, srid))

        return self._projection_units[srid]

    def get_projection_string(self, model_db, srid, proj_format=''):
        """
        Get the projection string as either wkt or proj4 format.

        Args:
            model_db(ModelDatabase): the object representing the model database.:
            srid(int): EPSG spatial reference identifier.
            proj_format(str): project string format (either SpatialManager.PRO_WKT or SpatialManager.PRO_PROJ4).

        Returns:
            str: projection string.
        """
        if not proj_format:
            proj_format = self.PRO_WKT

        if proj_format not in (self.PRO_WKT, self.PRO_PROJ4):
            raise ValueError('Invalid projection format given: {}. Use either SpatialManager.PRO_WKT or '
                             'SpatialManager.PRO_PROJ4.'.format(proj_format))

        if srid not in self._projection_string or proj_format not in self._projection_string[srid]:
            db_engine = model_db.get_engine()
            try:
                if proj_format is self.PRO_WKT:
                    sql = "SELECT srtext AS proj_string FROM spatial_ref_sys WHERE srid = {}".format(srid)
                else:
                    sql = "SELECT proj4text AS proj_string FROM spatial_ref_sys WHERE srid = {}".format(srid)

                ret = db_engine.execute(sql)
                projection_string = ''

                for row in ret:
                    projection_string = row.proj_string
            finally:
                db_engine.dispose()

            if srid not in self._projection_string:
                self._projection_string[srid] = {}

            self._projection_string[srid].update({proj_format: projection_string})

        return self._projection_string[srid][proj_format]

    def link_geoserver_to_db(self, model_db, reload_config=True):
        """
        Link GeoServer to a Model Database.

        Args:
            model_db(ModelDatabase): the object representing the model database.
            reload_config(bool): Reload the geoserver node configuration and catalog before returning if True.
        """
        db_url = model_db.db_url_obj

        self.gs_api.create_postgis_store(
            workspace=self.WORKSPACE,
            name=model_db.get_id(),
            db_host=db_url.host,
            db_port=db_url.port,
            db_name=db_url.database,
            db_username=db_url.username,
            db_password=db_url.password
        )

        if reload_config:
            self.reload(ports=self.gs_api.GEOSERVER_CLUSTER_PORTS, public_endpoint=False)

    def unlink_geoserver_from_db(self, model_db, purge=False, recurse=False):
        """
        Unlink GeoServer from a Model Database.

        Args:
            model_db(ModelDatabase): the object representing the model database.
            purge(bool): delete configuration files from filesystem if True.
            recurse(bool): recursively delete any dependent objects if True.
        """
        store_id = self.get_db_specific_store_id(model_db)
        response = self.gs_engine.delete_store(
            store_id,
            purge=purge,
            recurse=recurse,
        )
        return response

    def create_extent_layer(self, datastore_name, resource_id, reload_config=True):
        """
        Creates a GeoServer SQLView Layer for the extent from the resource.

        Args:
            datastore_name(str): name of the app database, for example: app_primary_db.
            resource_id(str): id of the extent record.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Get Default Style Name
        default_style = f'atcore:{self.VL_EXTENT_TEMPLATE}'

        # feature name
        feature_name = f'app_users_resources_{resource_id}'

        sql_context = {
            'resource_id': resource_id,
        }

        # Render SQL
        sql_template_file = os.path.join(self.SQL_PATH, self.VL_EXTENT_VIEW + '.sql')
        with open(sql_template_file, 'r') as sql_template_file:
            text = sql_template_file.read()
            template = Template(text)
            sql = ' '.join(template.render(sql_context).split())

        # Create SQL View
        self.gs_api.create_layer(
            workspace=self.WORKSPACE,
            datastore_name=datastore_name,
            feature_name=feature_name,
            geometry_type=self.GT_POLYGON,
            srid=4326,
            sql=sql,
            default_style=default_style,
        )

        if reload_config:
            self.reload(ports=self.gs_api.GEOSERVER_CLUSTER_PORTS, public_endpoint=public_endpoint)

    def delete_extent_layer(self, datastore_name, resource_id, recurse=True, reload_config=True):
        # feature name
        feature_name = f'app_users_resources_{resource_id}'

        self.gs_api.delete_layer(
            workspace=self.WORKSPACE,
            datastore_nam=datastore_name,
            name=resource_id,
            recurse=recurse,

        )

        if reload_config:
            self.reload(ports=self.gs_api.GEOSERVER_CLUSTER_PORTS, public_endpoint=public_endpoint)
