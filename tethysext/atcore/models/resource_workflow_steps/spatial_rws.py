"""
********************************************************************************
* Name: spatial_rws.py
* Author: nswain
* Created On: March 28, 2019
* Copyright: (c) Aquaveo 2019
******
"""
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class SpatialResourceWorkflowStep(ResourceWorkflowStep):
    """
    Abstract base class of all Spatial Resource Workflow Steps.
    """  # noqa: #501
    TYPE = 'spatial_resource_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    def __init__(self, geoserver_name, map_manager, spatial_manager, *args, **kwargs):
        """
        Constructor.

        Args:
            geoserver_name(str): Name of geoserver setting to use.
            map_manager(MapManager): Instance of MapManager to use for the map view.
            spatial_manager(SpatialManager): Instance of SpatialManager to use for the map view.
        """
        super().__init__(*args, **kwargs)
        self.controller_kwargs = {
            'geoserver_name': geoserver_name,
            '_MapManager': map_manager,
            '_SpatialManager': spatial_manager
        }
