"""
********************************************************************************
* Name: spatial_reference.py
* Author: nswain
* Created On: May 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


class SpatialReferenceService:
    """
    Used to lookup available spatial references dynamically.
    """

    def __init__(self, db_engine):
        """
        constructor.
        Args:
            db_engine(sqlalchemy.engine): engine with connection to spatial database with spatial_ref_sys table.
        """
        self.db_engine = db_engine

    def get_spatial_reference_system_by_srid(self, srid):
        """"
        Get a user friendly name for spatial reference system based on an SRID.

        Args:
            srid(str): EPSG spatial reference id as a string (e.g. 3566).
        """
        spatial_ref_list = []

        if not srid or srid == 'None':
            spatial_ref_list.append({"text": 'None', "id": 'None'})
            json = {'results': spatial_ref_list}
            return json

        # Retrieve a list of SRIDs from database
        get_spatial_ref_list = "SELECT * FROM spatial_ref_sys WHERE ({0} = @srid)".format(srid)

        spatial_ref_object_result = self.db_engine.execute(get_spatial_ref_list)

        # Parse out the wanted items into the list for the select input
        for spatial_reference in spatial_ref_object_result:
            spatial_ref_list.append(
                {
                    "text": "{0} {1}".format(spatial_reference[0], spatial_reference[3].split('"')[1]),
                    "id": str(spatial_reference[0])
                }
            )
        spatial_ref_object_result.close()

        json = {'results': spatial_ref_list}
        return json

    def get_spatial_reference_system_by_query_string(self, query_words):
        """"
        Get a user friendly name for spatial reference system based on a query string.

        Args:
            query_words(list): list of query parameters (e.g. ['Utah', 'Central'] ).
        """
        spatial_ref_list = []

        if len(query_words) == 1:
            sql_query_input = query_words[0]
        else:
            sql_query_input = ' & '.join(query_words)

        # Retrieve a list of SRIDs from database
        get_spatial_ref_list = "SELECT * FROM spatial_ref_sys " \
                               "WHERE to_tsvector('english', srtext) @@ " \
                               "to_tsquery('english', '{0}');".format(sql_query_input)

        spatial_ref_object_result = self.db_engine.execute(get_spatial_ref_list)

        # Parse out the wanted items into the list for the select input
        for spatial_reference in spatial_ref_object_result:
            spatial_ref_list.append(
                {
                    "text": "{0} {1}".format(spatial_reference[0], spatial_reference[3].split('"')[1]),
                    "id": str(spatial_reference[0])
                }
            )
        spatial_ref_object_result.close()

        json = {'results': spatial_ref_list}

        return json
