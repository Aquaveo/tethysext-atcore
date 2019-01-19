"""
********************************************************************************
* Name: spatial_manager
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from abc import ABCMeta, abstractmethod
from tethysext.atcore.services.geoserver_api import GeoServerAPI


def reload_config(public_endpoint=False, reload_config_default=True):
    """
    Decorator that handles config reload for methods of the SpatialManager class.

    Args:
        public_endpoint(bool): Use public GeoServer endpoint for the reload call.
        reload_config_default(bool): Default to use if the "reload_config" parameter is not specified.
    """
    def reload_decorator(method):
        def wrapper(*args, **kwargs):
            if not isinstance(args[0], BaseSpatialManager):
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


class BaseSpatialManager(object):
    """
    Base class for SpatialManagers.
    """
    __metaclass__ = ABCMeta

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

    @abstractmethod
    def get_extent_for_project(self, *args, **kwargs):
        """
        Get extent of the project.

        """
        pass

    @abstractmethod
    def get_projection_units(self, *args, **kwargs):
        """
        Get units of the given projection.

        """
        pass

    @abstractmethod
    def get_projection_string(self, *args, **kwargs):
        """
        Get the projection string as either wkt or proj4 format.

        """
        pass

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

    def reload(self, ports=None, public_endpoint=True):
        """
        Reload the in memory catalog of each member of the geoserver cluster.
        """
        self.gs_api.reload(ports, public_endpoint)
