"""
********************************************************************************
* Name: spatial_rws.py
* Author: nswain
* Created On: March 28, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import json
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class SpatialResourceWorkflowStep(ResourceWorkflowStep):
    """
    Abstract base class of all Spatial Resource Workflow Steps.
    """  # noqa: #501
    TYPE = 'spatial_resource_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'geocode_enabled': False,
            'label_property': None,
        })
        return default_options

    def __init__(self, geoserver_name, map_manager, spatial_manager, *args, **kwargs):
        """
        Constructor.

        Args:
            geoserver_name(str): Name of geoserver setting to use.
            map_manager(MapManager): Instance of MapManager to use for the map view.
            spatial_manager(SpatialManager): Instance of SpatialManager to use for the map view.
        """
        super().__init__(*args, **kwargs)
        self.controller.kwargs = {
            'geoserver_name': geoserver_name,
            '_MapManager': map_manager,
            '_SpatialManager': spatial_manager
        }

    def to_geojson(self, as_str=False):
        """
        Serialize SpatialResourceWorkflowStep to GeoJSON.

        Args:
            as_str(bool): Returns GeoJSON string if True, otherwise returns dict equivalent.

        Returns:
            str or dict: GeoJSON string or dict equivalent representation of the spatial portions of a SpatialResourceWorkflowStep.
        """  # noqa: E501
        geojson_dict = self.get_parameter('geometry')

        if as_str:
            return json.dumps(geojson_dict)

        return geojson_dict
