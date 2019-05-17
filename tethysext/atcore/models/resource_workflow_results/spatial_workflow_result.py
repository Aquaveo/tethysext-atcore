"""
********************************************************************************
* Name: spatial_workflow_result
* Author: nswain
* Created On: April 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult


__all__ = ['SpatialWorkflowResults']


class SpatialWorkflowResults(ResourceWorkflowResult):
    """
    Data model for storing spatial information about resource workflow results.
    """
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView'  # noqa: E501
    TYPE = 'spatial_workflow_result'

    __mapper_args__ = {
        'polymorphic_on': 'type',
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
        self.controller.kwargs = {
            'geoserver_name': geoserver_name,
            '_MapManager': map_manager,
            '_SpatialManager': spatial_manager
        }
