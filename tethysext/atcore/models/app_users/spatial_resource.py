"""
********************************************************************************
* Name: spatial_resource.py
* Author: glarsen
* Created On: November 17, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import json
from typing import Union

from sqlalchemy import func, inspect, Column
from geoalchemy2.types import Geometry

from tethysext.atcore.exceptions import InvalidSpatialResourceExtentTypeError
from tethysext.atcore.models.app_users.resource import Resource

__all__ = ['SpatialResource']


class SpatialResource(Resource):
    # Resource Types
    TYPE = 'spatial_resource'
    DISPLAY_TYPE_SINGULAR = 'Spatial Resource'
    DISPLAY_TYPE_PLURAL = 'Spatial Resources'

    extent = Column(Geometry)

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }

    def set_extent(self, obj: Union[dict, str], object_format: str = 'dict'):
        """
        Set the extent for the SpatialResource.

        Args:
            obj: A string or a dict representing the extent.
            object_format (str): A string defining the type of obj. One of 'wkt', 'geojson', and 'dict'.
        """
        if object_format not in ['dict', 'wkt', 'geojson']:
            raise InvalidSpatialResourceExtentTypeError(f'"{object_format}" is not a valid type for a SpatialResource '
                                                        f'extent. Must be one of "wkt", "geojson", or "dict"')
        object_to_convert = obj
        if object_format == 'dict':
            object_to_convert = json.dumps(obj)
        session = inspect(self).session
        if object_format == 'wkt':
            qry = session.query(func.ST_GeomFromEWKT(object_to_convert).label('geom'))
            new_extent = qry.first().geom
        else:
            qry = session.query(func.ST_GeomFromGeoJSON(object_to_convert).label('geom'))
            new_extent = qry.first().geom
        self.extent = new_extent

    def get_extent(self, extent_type: str = 'dict'):
        """
        Get the extent from the SpatialResource.

        Args:
            extent_type (str): The format that should be returned for the extent. One of 'wkt', 'geojson', and 'dict'.
        """
        if extent_type not in ['dict', 'wkt', 'geojson']:
            raise InvalidSpatialResourceExtentTypeError(f'"{extent_type}" is not a valid type for a SpatialResource '
                                                        f'extent. Must be one of "wkt", "geojson", or "dict"')

        if self.extent is None:
            return None

        session = inspect(self).session
        if extent_type == 'wkt':
            qry = session.query(func.ST_AsEWKT(self.extent).label('extent'))
        else:
            qry = session.query(func.ST_AsGeoJSON(self.extent).label('extent'))
        extent = qry.first().extent
        if extent_type == 'dict':
            extent = json.loads(extent)
        return extent
