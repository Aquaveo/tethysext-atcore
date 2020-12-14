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
from tethysext.atcore.models.app_users import Resource


class ResourceSpatialManager(BaseSpatialManager):
    """
    Class for Spatial Managers using a postgres database.
    """

    SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sql_templates')
    SLD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sld_templates')

    # Vector Layer Types
    VL_EXTENT_VIEW = 'resource_extent_layer_view'
    VL_EXTENT_TEMPLATE = 'resource_extent_layer_style'

    def get_extent_for_project(self, datastore_name, resource_id):
        """
        Get the extent. This will return the list of the extent in EPSG 4326.
        The query in resource_extent_layer_view transforms all features to 4326.

        Args:
            datastore_name(str): name of the app database, for example: app_primary_db.
            resource_id(str): id of the extent record.
        """
        # feature name
        feature_name = f'app_users_resources_{resource_id}'

        extent = self.gs_api.get_layer_extent(
            workspace=self.WORKSPACE,
            datastore_name=datastore_name,
            feature_name=feature_name,
        )

        return extent

    def get_projection_units(self, resource, srid):
        pass

    def get_projection_string(self, model_db, srid, proj_format=''):
        pass

    def create_extent_layer(self, datastore_name, resource_id):
        """
        Creates a GeoServer SQLView Layer for the extent from the resource.

        Args:
            datastore_name(str): name of the app database, for example: app_primary_db.
            resource_id(str): id of the extent record.
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

    def delete_extent_layer(self, datastore_name, resource_id, recurse=True):
        # feature name
        feature_name = f'app_users_resources_{resource_id}'

        self.gs_api.delete_layer(
            workspace=self.WORKSPACE,
            datastore_nam=datastore_name,
            name=feature_name,
            recurse=recurse,
        )
