"""
********************************************************************************
* Name: spatial_manager
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.services.exceptions import UnitsNotFound, UnknownUnits
from tethysext.atcore.services.geoserver_api import GeoServerAPI


def reload_config(public_endpoint=False, reload_config_default=True):
    """
    Decorator that handles config reload for methods of the GsshaSpatialManager class.

    Args:
        public_endpoint(bool): Use public GeoServer endpoint for the reload call.
        reload_config_default(bool): Default to use if the "reload_config" parameter is not specified.
    """
    def reload_decorator(method):
        def wrapper(*args, **kwargs):
            if not isinstance(args[0], SpatialManager):
                raise ValueError('The "reload_config" decorator can only be used on methods of SpatialManager '
                                 'dervied classes.')

            # Call the method
            return_value = method(*args, **kwargs)

            # Call handle reload_config parameter
            if 'reload_config' in kwargs:
                should_reload = kwargs['reload_config']
            else:
                should_reload = reload_config_default

            if should_reload:
                self = args[0]
                self.reload(ports=self.gs_api.GEOSERVER_CLUSTER_PORTS, public_endpoint=public_endpoint)
            return return_value

        return wrapper

    return reload_decorator


class SpatialManager(object):
    """
    Base class for SpatialManagers.
    """
    SQL_PATH = ''
    SLD_PATH = ''
    WORKSPACE = 'my-app'
    URI = 'http://app.aquaveo.com/my-app'

    # Suffixes
    LEGEND_SUFFIX = 'legend'
    LABELS_SUFFIX = 'labels'
    GLOBAL_SUFFIX = 'global'

    GT_POLYGON = 'Polygon'
    GT_LINE = 'LineString'
    GT_POINT = 'Point'
    GT_RASTER = 'Raster'

    U_METRIC = 'metric'
    U_IMPERIAL = 'imperial'

    PRO_WKT = 'srtext'
    PRO_PROJ4 = 'proj4text'

    def __init__(self, geoserver_engine):
        """
        Constructor

        Args:
            workspace(str): The workspace to use when creating layers and styles.
            geoserver_engine(tethys_dataset_services.GeoServerEngine): Tethys geoserver engine.
        """
        self.gs_engine = geoserver_engine
        self.gs_api = GeoServerAPI(geoserver_engine)
        self._projection_units = {}
        self._projection_string = {}

    def get_ows_endpoint(self, public_endpoint=True):
        """
        Returns the GeoServer endpoint for OWS services (with trailing slash).

        Args:
            public_endpoint(bool): return with the public endpoint if True.
        """
        return self.gs_api.get_ows_endpoint(self.WORKSPACE, public_endpoint)

    def get_wms_endpoint(self, public=True):
        """
        Returns the GeoServer endpoint for WMS services (with trailing slash).

        Args:
            public(bool): return with the public endpoint if True.
        """
        return self.gs_api.get_wms_endpoint(public)

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

    def get_projection_string(self, model_db, srid, format=PRO_WKT):
        """
        Get the projection string as either wkt or proj4 format.

        Args:
            model_db(ModelDatabase): the object representing the model database.:
            srid(int): EPSG spatial reference identifier.
            format(str): project string format (either SpatialManager.PRO_WKT or SpatialManager.PRO_PROJ4).

        Returns:
            str: projection string.
        """
        if format not in (self.PRO_WKT, self.PRO_PROJ4):
            raise ValueError('Invalid projection format given: {}. Use either SpatialManager.PRO_WKT or '
                             'SpatialManager.PRO_PROJ4.'.format(format))

        if srid not in self._projection_string or format not in self._projection_string[srid]:
            db_engine = model_db.get_engine()
            try:
                if format is self.PRO_WKT:
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

            self._projection_string[srid].update({format: projection_string})

        return self._projection_string[srid][format]

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

    def create_workspace(self):
        """
        Create workspace.
        """
        self.gs_engine.create_workspace(self.WORKSPACE, self.URI)

        # Reload configuration on all slave nodes to perpetuate styles
        self.reload(ports=self.gs_api.GEOSERVER_CLUSTER_PORTS, public_endpoint=False)

        return True

    def get_db_specific_store_id(self, model_db):
        """
        Construct the model database specific store id.

        Args:
            model_db(ModelDatabase): the object representing the model database.
        """
        return '{0}:{1}'.format(self.WORKSPACE, model_db.get_id())

    def reload(self, ports=None, public_endpoint=True):
        """
        Reload the in memory catalog of each member of the geoserver cluster.
        """
        self.gs_api.reload(ports, public_endpoint)