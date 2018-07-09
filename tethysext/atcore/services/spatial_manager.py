"""
********************************************************************************
* Name: spatial_manager
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.services.geoserver_api import GeoServerAPI


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

    def __init__(self, geoserver_engine):
        """
        Constructor

        Args:
            workspace(str): The workspace to use when creating layers and styles.
            geoserver_engine(tethys_dataset_services.GeoServerEngine): Tethys geoserver engine.
        """
        self.gs_engine = geoserver_engine
        self.gs_api = GeoServerAPI(geoserver_engine)

    def get_ows_endpoint(self, public_endpoint=True):
        """
        Returns the GeoServer endpoint for OWS services (with trailing slash).

        Args:
            public_endpoint (bool): return with the public endpoint if True.
        """
        return self.gs_api.get_ows_endpoint(self.WORKSPACE, public_endpoint)

    def get_wms_endpoint(self, public=True):
        """
        Returns the GeoServer endpoint for WMS services (with trailing slash).

        Args:
            public (bool): return with the public endpoint if True.
        """
        return self.gs_api.get_wms_endpoint(public)

    def link_geoserver_to_db(self, model_db, reload_config=True):
        """
        Link GeoServer to a Model Database.

        Args:
            model_db (ModelDatabase): the object representing the model database.
            reload_config (bool): Reload the geoserver node configuration and catalog before returning if True.
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
            model_db (ModelDatabase): the object representing the model database.
            purge (bool): delete configuration files from filesystem if True.
            recurse (bool): recursively delete any dependent objects if True.
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
            model_db (ModelDatabase): the object representing the model database.
        """
        return '{0}:{1}'.format(self.WORKSPACE, model_db.get_id())

    def reload(self, ports=None, public_endpoint=True):
        """
        Reload the in memory catalog of each member of the geoserver cluster.
        """
        self.gs_api.reload(ports, public_endpoint)
