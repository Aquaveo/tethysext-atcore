"""
********************************************************************************
* Name: spatial_reference.py
* Author: nswain
* Created On: May 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.http import JsonResponse
from tethys_apps.base.controller import TethysController
from tethysext.atcore.services.spatial_reference import SpatialReferenceService


class QuerySpatialReference(TethysController):
    """
    Controller for modify_resource page.

    POST: Handle spatial reference queries.
    """
    _app = None
    _persistent_store_name = None
    _SpatialReferenceService = SpatialReferenceService

    def get(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        if request.GET.get('id', False):
            return self.query_srid_by_id(request)
        elif request.GET.get('q', False):
            return self.query_srid_by_query(request)
        elif request.GET.get('wkt', False):
            return self.query_wkt_by_id(request)

        return JsonResponse({'error': 'BadRequest: must pass either "id", "q", or "wkt" parameters.'})

    def query_srid_by_id(self, request):
        """"
        This controller is normally called by the select2 Ajax for looking up SRIDs from the SQL database
        """
        srid = request.GET.get('id', '')
        _engine = self.get_engine()
        srs = self._SpatialReferenceService(_engine)
        dict = srs.get_spatial_reference_system_by_srid(srid)
        return JsonResponse(dict)

    def query_wkt_by_id(self, request):
        """"
        This controller is normally called by the select2 Ajax for looking up SRIDs from the SQL database
        """
        srid = request.GET.get('wkt', '')
        _engine = self.get_engine()
        srs = self._SpatialReferenceService(_engine)
        dict = srs.get_wkt_by_srid(srid)
        return JsonResponse(dict)

    def query_srid_by_query(self, request):
        """"
        This controller is normally called by the select2 Ajax for looking up SRIDs from the SQL database
        """
        query_words = request.GET.get('q', '').split()
        _engine = self.get_engine()
        srs = self._SpatialReferenceService(_engine)
        dict = srs.get_spatial_reference_system_by_query_string(query_words)
        return JsonResponse(dict)

    def get_engine(self):
        """
        Get connection to database.
        Returns:
            sqlalchemy.engine: connection to database with spatial_ref_sys table.
        """
        if not self._app:
            raise NotImplementedError('_app not implemented for QuerySpatialReference controller.')
        if not self._persistent_store_name:
            raise NotImplementedError('_persistent_store_name not implemented for QuerySpatialReference controller.')
        return self._app.get_persistent_store_database(self._persistent_store_name)
