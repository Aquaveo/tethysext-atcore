"""
********************************************************************************
* Name: resource_spatial_manager
* Author: nswain, msouffront & htran
* Created On: December 15, 2020
* Updated on: December 15, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
import os
from jinja2 import Template

from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager

log = logging.getLogger(f'tethys.{__name__}')


class ResourceSpatialManager(BaseSpatialManager):
    """
    A generic SpatialManger for SpatialResource.
    """

    SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sql_templates')
    SLD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sld_templates')

    # Vector Layer Types
    VL_EXTENT_VIEW = 'resource_extent_layer_view'
    VL_EXTENT_STYLE = 'resource_extent_layer_style'

    def get_projection_units(self, *args, **kwargs):
        """
        Get units of the given projection.

        """
        return "<units>"

    def get_projection_string(self, *args, **kwargs):
        """
        Get the projection string as either wkt or proj4 format.

        """
        return "<projection string>"

    def get_extent_layer_name(self, resource_id):
        """
        Get name of the extent layer for a given resource.

        Args:
            resource_id(str): id of the Resource.

        Returns:
            str: name of the extent layer.

        """
        return f'app_users_resources_extent_{resource_id}'

    def get_extent_for_project(self, datastore_name, resource_id):
        """
        Get the extent. This will return the list of the extent in EPSG 4326.
        The query in resource_extent_layer_view transforms all features to 4326.

        Args:
            datastore_name(str): name of the PostGIS datastore in GeoServer that contains the layer data.
             For example: app_primary_db.
            resource_id(str): id of the Resources.
        """
        # feature name
        feature_name = self.get_extent_layer_name(resource_id)

        extent = self.gs_api.get_layer_extent(
            workspace=self.WORKSPACE,
            datastore_name=datastore_name,
            feature_name=feature_name,
        )

        return extent

    def get_resource_extent_wms_url(self, resource):
        """
        Get url for map preview image.
        Returns:
            str: preview image url.
        """
        # Default image url
        layer_preview_url = None
        layer_name = f'{self.WORKSPACE}:{self.get_extent_layer_name(resource.id)}'
        try:
            extent = self.get_extent_for_project(datastore_name=f'{self.WORKSPACE}_primary_db',
                                                 resource_id=str(resource.id))

            # Calculate preview layer height and width ratios
            if extent:
                # Calculate image dimensions
                long_dif = abs(extent[0] - extent[2])
                lat_dif = abs(extent[1] - extent[3])
                hw_ratio = float(long_dif) / float(lat_dif)
                max_dim = 300

                if hw_ratio < 1:
                    width_resolution = int(hw_ratio * max_dim)
                    height_resolution = max_dim
                else:
                    height_resolution = int(max_dim / hw_ratio)
                    width_resolution = max_dim

                wms_endpoint = self.get_wms_endpoint()

                layer_preview_url = f'{wms_endpoint}?service=WMS&version=1.1.0&request=GetMap&layers={layer_name}' \
                                    f'&bbox={extent[0]},{extent[1]},{extent[2]},{extent[3]}&width={width_resolution}' \
                                    f'&height={height_resolution}&srs=EPSG:4326&format=image%2Fpng'
        except Exception:
            log.exception('An error occurred while trying to generate the preview image.')

        return layer_preview_url

    def create_extent_layer(self, datastore_name, resource_id, geometry_type=None, srid=4326):
        """
        Creates a GeoServer SQLView Layer for the extent from the resource.

        Args:
            datastore_name(str): name of the PostGIS datastore in GeoServer that contains the layer data.
             For example: app_primary_db.
            resource_id(str): id of the Resources.
            geometry_type(str): type of geometry. Pick from: Polygon, LineString, Point.
            srid(str): Spatial Reference Identifier of the extent. Default to 4326.
        """
        geometry_check_list = [x.lower() for x in [self.GT_POLYGON, self.GT_LINE, self.GT_POINT]]
        if geometry_type is None:
            geometry_type = self.GT_POLYGON

        if geometry_type.lower() not in geometry_check_list:
            raise ValueError(f'{geometry_type} is an invalid geometry type. The type must be from one of the '
                             f'following: Polygon, LineString or Point')

        # Get Default Style Name
        default_style = f'atcore:{self.VL_EXTENT_STYLE}'

        # feature name
        feature_name = self.get_extent_layer_name(resource_id=resource_id)

        sql_context = {
            'resource_id': resource_id,
            'srid': srid,
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
            srid=srid,
            sql=sql,
            default_style=default_style,
        )

    def delete_extent_layer(self, datastore_name, resource_id, recurse=True):
        """
        Delete a given geoserver layer.

        Args:
            datastore_name(str): name of the PostGIS datastore in GeoServer that contains the layer data.
             For example: app_primary_db.
            resource_id(str): id of the Resources.
            recurse (bool): recursively delete any dependent objects if True.
        """
        feature_name = self.get_extent_layer_name(resource_id=resource_id)

        self.gs_api.delete_layer(
            workspace=self.WORKSPACE,
            datastore=datastore_name,
            name=feature_name,
            recurse=recurse,
        )
