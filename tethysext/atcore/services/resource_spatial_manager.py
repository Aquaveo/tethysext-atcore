"""
********************************************************************************
* Name: resource_spatial_manager
* Author: nswain, msouffront & htran
* Created On: December 15, 2020
* Updated on: December 15, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
from jinja2 import Template

from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager


class ResourceSpatialManager(BaseSpatialManager):
    """
    A generic SpatialManger for SpatialResource.
    """

    SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sql_templates')
    SLD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sld_templates')

    # Vector Layer Types
    VL_EXTENT_VIEW = 'resource_extent_layer_view'
    VL_EXTENT_STYLE = 'resource_extent_layer_style'

    def get_extent_layer_name(self, resource_id):
        """
        Get name of the extent layer for a given resource.

        Args:
            resource_id(str): id of the Resource.

        Returns:
            str: name of the extent layer.

        """
        return f'app_users_resources_{resource_id}'

    def get_extent_for_project(self, datastore_name, resource_id):
        """
        Get the extent. This will return the list of the extent in EPSG 4326.
        The query in resource_extent_layer_view transforms all features to 4326.

        Args:
            datastore_name(str): name of the app database, for example: app_primary_db.
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

    def create_extent_layer(self, datastore_name, resource_id, geometry_type=None):
        """
        Creates a GeoServer SQLView Layer for the extent from the resource.

        Args:
            datastore_name(str): name of the app database, for example: app_primary_db.
            resource_id(str): id of the Resources.
            geometry_type(str): type of geometry. Pick from: Polygon, LineString, Point.
        """
        geometry_check_list = [x.lower() for x in [self.GT_POLYGON, self.GT_LINE, self.GT_POINT]]
        if geometry_type is None or geometry_type.lower() not in geometry_check_list:
            geometry_type = self.GT_POLYGON

        # Get Default Style Name
        default_style = f'atcore:{self.VL_EXTENT_STYLE}'

        # feature name
        feature_name = self.get_extent_layer_name(resource_id=resource_id)

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

    def delete_extent_layer(self, datastore_name, resource_id, recurse=True):
        """
        Delete a given geoserver layer.

        Args:
            datastore_name(str): name of the app database, for example: app_primary_db.
            resource_id(str): id of the Resources.
            recurse (bool): recursively delete any dependent objects if True.
        """
        feature_name = self.get_extent_layer_name(resource_id=resource_id)

        self.gs_api.delete_layer(
            workspace=self.WORKSPACE,
            datastore_name=datastore_name,
            name=feature_name,
            recurse=recurse,
        )
