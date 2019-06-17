"""
********************************************************************************
* Name: spatial_input_mwv.py
* Author: nswain
* Created On: January 21, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import json
import os
import zipfile
import uuid
import shutil
import shapefile as shp
import geojson
import logging
from django.shortcuts import redirect
from tethys_sdk.gizmos import MVDraw
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS


log = logging.getLogger(__name__)


class SpatialInputMWV(MapWorkflowView):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    template_name = 'atcore/resource_workflows/spatial_input_mwv.html'
    valid_step_classes = [SpatialInputRWS]

    def get_step_specific_context(self, request, session, context, current_step, previous_step, next_step):
        """
        Hook for extending the view context.

        Args:
           request(HttpRequest): The request.
           session(sqlalchemy.orm.Session): Session bound to the steps.
           context(dict): Context object for the map view template.
           current_step(ResourceWorkflowStep): The current step to be rendered.
           previous_step(ResourceWorkflowStep): The previous step.
           next_step(ResourceWorkflowStep): The next step.

        Returns:
            dict: key-value pairs to add to context.
        """
        return {'allow_shapefile': current_step.options['allow_shapefile']}

    def process_step_options(self, request, session, context, resource, current_step, previous_step, next_step):
        """
        Hook for processing step options (i.e.: modify map or context based on step options).

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            context(dict): Context object for the map view template.
            resource(Resource): the resource for this request.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        """
        # Get Map View
        map_view = context['map_view']

        # Turn off feature selection
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Add layer for current geometry
        enabled_controls = ['Modify', 'Delete', 'Move', 'Pan']
        if current_step.options['allow_drawing']:
            for elem in current_step.options['shapes']:
                if elem == 'points':
                    enabled_controls.append('Point')
                elif elem == 'lines':
                    enabled_controls.append('LineString')
                elif elem == 'polygons':
                    enabled_controls.append('Polygon')
                elif elem == 'extents':
                    enabled_controls.append('Box')
                else:
                    raise ValueError('Invalid shapes defined: {}.'.format(elem))

        # Load the currently saved geometry, if any.
        current_geometry = current_step.get_parameter('geometry')

        # Configure drawing
        draw_options = MVDraw(
            controls=enabled_controls,
            initial='Pan',
            initial_features=current_geometry,
            output_format='GeoJSON',
            snapping_enabled=current_step.options['snapping_enabled'],
            snapping_layer=current_step.options['snapping_layer'],
            snapping_options=current_step.options['snapping_options']
        )

        if draw_options is not None and 'map_view' in context:
            map_view.draw = draw_options

        # Save changes to map view
        context.update({'map_view': map_view})

    def process_step_data(self, request, session, step, model_db, current_url, previous_url, next_url):
        """
        Hook for processing user input data coming from the map view. Process form data found in request.POST and request.GET parameters and then return a redirect response to one of the given URLs.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            step(ResourceWorkflowStep): The step to be updated.
            model_db(ModelDatabase): The model database associated with the resource.
            current_url(str): URL to step.
            previous_url(str): URL to the previous step.
            next_url(str): URL to the next step.

        Returns:
            HttpResponse: A Django response.

        Raises:
            ValueError: exceptions that occur due to user error, provide helpful message to help user solve issue.
            RuntimeError: exceptions that require developer attention.
        """  # noqa: E501
        # Prepare POST parameters
        geometry = request.POST.get('geometry', None)
        shapefile = request.FILES.get('shapefile', None)

        # Validate input (need at least geometry or shapefile)
        if not geometry and not shapefile:
            # Don't require input to go back
            if 'previous-submit' in request.POST:
                return redirect(previous_url)

            # Raise error if going forward
            else:
                step.set_parameter('geometry', None)
                session.commit()
                raise ValueError('You must either draw at least one shape or upload a shapefile.')

        # Handle File parameter
        shapefile_geojson = self.parse_shapefile(request, shapefile)

        # Handle geometry parameter
        geometry_geojson = self.parse_drawn_geometry(geometry)

        # Combine the geojson objects.
        combined_geojson = self.combine_geojson_objects(shapefile_geojson, geometry_geojson)

        # Post process geojson
        post_processed_geojson = self.post_process_geojson(combined_geojson)

        # Update the geometry parameter
        step.set_parameter('geometry', post_processed_geojson)

        # Validate the Parameters
        step.validate()

        # Update the status of the step
        step.set_status(step.ROOT_STATUS_KEY, step.STATUS_COMPLETE)
        step.set_attribute(step.ATTR_STATUS_MESSAGE, None)
        session.commit()

        # If shapefile is given, reload current step to show user the features loaded from the shapefile
        if shapefile:
            response = redirect(current_url)

        # Otherwise, go to the next step
        else:
            response = super().process_step_data(request, session, step, model_db, current_url, previous_url, next_url)

        return response

    def parse_shapefile(self, request, in_memory_file):
        """
        Parse shapefile, serialize into GeoJSON, and validate.
        Args:
            request(HttpRequest): The request.
            in_memory_file (InMemoryUploadedFile): A zip archive containing the shapefile that has been uploaded.

        Returns:
            dict: Dictionary equivalent of GeoJSON.
        """
        workdir = None

        if not in_memory_file:
            return None

        try:
            # Write file to workspace temporarily
            user_workspace = self.get_app().get_user_workspace(request.user)
            workdir = os.path.join(user_workspace.path, str(uuid.uuid4()))

            if not os.path.isdir(workdir):
                os.mkdir(workdir)

            # Write in-memory file to disk
            filename = os.path.join(workdir, in_memory_file.name)
            with open(filename, 'wb') as f:
                for chunk in in_memory_file.chunks():
                    f.write(chunk)

            # Unzip
            if zipfile.is_zipfile(filename):
                with zipfile.ZipFile(filename, 'r') as z:
                    z.extractall(workdir)

            # Convert shapes to geojson
            features = []
            for f in os.listdir(workdir):
                if '.shp' not in f:
                    continue

                path = os.path.join(workdir, f)
                reader = shp.Reader(path)
                fields = reader.fields[1:]
                field_names = [field[0] for field in fields]

                for sr in reader.shapeRecords():
                    attributes = dict(zip(field_names, sr.record))
                    geometry = sr.shape.__geo_interface__
                    features.append({
                        'type': 'Feature',
                        'geometry': geometry,
                        'properties': attributes
                    })

            geojson_dicts = {
                'type': 'FeatureCollection',
                'features': features
            }

            # Convert to geojson objects
            geojson_str = json.dumps(geojson_dicts)
            geojson_objs = geojson.loads(geojson_str)

            # Validate
            if not geojson_objs.is_valid:
                raise RuntimeError('Invalid geojson from "shapefile" parameter: {}'.format(geojson_dicts))

        except shp.ShapefileException:
            raise ValueError('Invalid shapefile provided.')
        except Exception as e:
            raise RuntimeError('An error has occured while parsing the shapefile: {}'.format(e))

        finally:
            # Clean up
            workdir and shutil.rmtree(workdir)

        return geojson_objs

    @staticmethod
    def parse_drawn_geometry(geometry):
        """
        Parse the geometry into GeoJSON and validate.

        Args:
            geometry (str): GeoJSON string containing at least one feature.

        Returns:
            dict: Dictionary equivalent of GeoJSON.
        """
        if not geometry:
            return None

        geojson_objs = geojson.loads(geometry)

        geojson_objs = {
            'type': 'FeatureCollection',
            'features': geojson_objs.geometries
        }

        # Convert to geojson objects
        geojson_str = json.dumps(geojson_objs)
        geojson_objs = geojson.loads(geojson_str)

        if not geojson_objs.is_valid:
            raise RuntimeError('Invalid geojson from "geometry" parameter: {}'.format(geometry))

        return geojson_objs

    @staticmethod
    def combine_geojson_objects(shapefile_geojson, geometry_geojson):
        """
        Merge two geojson objects.
        Args:
            shapefile_geojson: geojson object derived from shapefile.
            geometry_geojson: geojson object derived from drawing.

        Returns:
            object: geojson object.
        """
        if shapefile_geojson is not None and geometry_geojson is None:
            return shapefile_geojson

        if shapefile_geojson is None and geometry_geojson is not None:
            return geometry_geojson

        shapefile_geojson['features'] += geometry_geojson['features']
        return shapefile_geojson

    @staticmethod
    def post_process_geojson(geojson):
        """
        Standardize GeoJSON format and add IDs. Note: OpenLayers is pretty finicky about the format of the geojson for mapping properties to the ol.Feature objects.

        Args:
            geojson: geojson object derived from input (drawing and/or shapefile.

        Returns:
            object: geojson object.
        """  # noqa: E501
        post_processed_geojson = {
            'type': 'FeatureCollection',
            'crs': {
                'type': 'name',
                'properties': {
                    'name': 'EPSG:4326'
                }
            },
            'features': []
        }

        if not geojson or 'features' not in geojson:
            return geojson

        # Sort the features for consistent ID'ing
        s_features = sorted(geojson['features'], key=lambda f: f.coordinates)

        for i, feature in enumerate(s_features):
            if 'type' not in feature or 'coordinates' not in feature:
                continue

            processed_feature = {
                'type': 'Feature',
                'geometry': {
                    'type': feature['type'],
                    'coordinates': feature['coordinates']
                },
                'properties': feature['properties'] if 'properties' in feature else {}
            }

            # Generate ID if not given
            if 'id' not in feature['properties']:
                feature['properties']['id'] = str(uuid.uuid4())

            post_processed_geojson['features'].append(processed_feature)

        return post_processed_geojson
