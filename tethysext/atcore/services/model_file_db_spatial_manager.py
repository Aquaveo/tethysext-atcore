"""
********************************************************************************
* Name: spatial_manager
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from abc import abstractmethod
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager


class ModelFileDBSpatialManager(BaseSpatialManager):
    """
    Class for SpatialManagers using a file database
    """

    @abstractmethod
    def get_extent_for_project(self, *args, **kwargs):
        """
        Return the extent / bounding box for a project/model.
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

        Args:
            model_db(ModelDatabase): the object representing the model database.:
            srid(int): EPSG spatial reference identifier.
            proj_format(str): project string format (either SpatialManager.PRO_WKT or SpatialManager.PRO_PROJ4).

        Returns:
            str: projection string.
        """
        pass
