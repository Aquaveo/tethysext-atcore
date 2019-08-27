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
from django.http import JsonResponse
from tethys_sdk.gizmos import MVDraw
from tethysext.atcore.forms.widgets.param_widgets import generate_django_form
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
        # Determine if user has an active role
        user_has_active_role = self.user_has_active_role(request, current_step)

        if user_has_active_role:
            allow_shapefile_uploads = current_step.options['allow_shapefile']
        else:
            allow_shapefile_uploads = False

        return {'allow_shapefile': allow_shapefile_uploads,
                'allow_edit_attributes': user_has_active_role}

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
        # Prepare attributes form
        attributes = current_step.options.get('attributes', None)

        if attributes is not None:
            attributes_form = generate_django_form(attributes)
            context.update({'attributes_form': attributes_form})

        # Get Map View
        map_view = context['map_view']

        # Determine if user has an active role
        user_has_active_role = self.user_has_active_role(request, current_step)

        # Turn off feature selection
        self.set_feature_selection(map_view=map_view, enabled=False)

        if user_has_active_role:
            enabled_controls = ['Modify', 'Delete', 'Move', 'Pan']

            # Add layer for current geometry
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
                        raise RuntimeError('Invalid shapes defined: {}.'.format(elem))
        else:
            enabled_controls = ['Pan']

        # Load the currently saved geometry, if any.
        current_geometry = current_step.get_parameter('geometry')

        # Configure drawing
        draw_options = MVDraw(
            controls=enabled_controls,
            initial='Pan',
            initial_features=current_geometry,
            output_format='GeoJSON',
            snapping_enabled=current_step.options.get('snapping_enabled'),
            snapping_layer=current_step.options.get('snapping_layer'),
            snapping_options=current_step.options.get('snapping_options'),
            feature_selection=attributes is not None,
            legend_title=current_step.options.get('plural_name'),
            data={
                'layer_id': 'drawing_layer',
                'layer_name': 'drawing_layer',
                'popup_title': current_step.options.get('singular_name'),
                'excluded_properties': ['id', 'type'],
            }
        )

        if draw_options is not None and 'map_view' in context:
            map_view.draw = draw_options

        # Save changes to map view
        context.update({'map_view': map_view})

        # Note: new layer created by super().process_step_options will have feature selection enabled by default
        super().process_step_options(
            request=request,
            session=session,
            context=context,
            resource=resource,
            current_step=current_step,
            previous_step=previous_step,
            next_step=next_step
        )

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
                raise ValueError(f'You must either draw at least one '
                                 f'{step.options.get("singular_name", "shape").lower()} or upload a shapefile of '
                                 f'{step.options.get("plural_name", "shapes").lower()}.')

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
        session.commit()

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
            response = super().process_step_data(
                request=request,
                session=session,
                step=step,
                model_db=model_db,
                current_url=current_url,
                previous_url=previous_url,
                next_url=next_url
            )

        return response

    def validate_feature_attributes(self, request, session, resource, step_id, *args, **kwargs):
        """
        Handle feature attribute validation AJAX requests.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            resource(Resource): the resource for this request.
            step_id(str): ID of the step to render.

        Returns:
            JsonResponse
        """
        step = self.get_step(request, step_id, session=session)
        attributes = request.POST.dict()
        attributes.pop('csrfmiddlewaretoken', None)
        attributes.pop('method', None)
        response = {'success': True}

        try:
            step.validate_feature_attributes(attributes)
        except ValueError as e:
            response.update({
                'success': False,
                'error': str(e)
            })

        return JsonResponse(response)

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
            projection_found = False
            shapefile_found = False

            for f in os.listdir(workdir):
                if '.shp' in f and '.shp.' not in f:
                    shapefile_found = True
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
                elif '.prj' in f:
                    # Check the projection
                    projection_found = True
                    path = os.path.join(workdir, f)

                    with open(path, 'r') as prj:
                        proj_str = prj.read()
                        self.validate_projection(proj_str)

            if not shapefile_found:
                raise ValueError('No shapefile found in given files.')

            if not projection_found:
                raise ValueError('Unable to determine projection of the given shapefile. Please include a .prj file.')

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

        except (ValueError, shp.ShapefileException) as e:
            raise ValueError(f'Invalid shapefile provided: {e}')
        except Exception as e:
            raise RuntimeError('An error has occurred while parsing the shapefile: {}'.format(e))

        finally:
            # Clean up
            workdir and shutil.rmtree(workdir)

        return geojson_objs

    def validate_projection(self, proj_str):
        """
        Validate the projection of uploaded shapefiles. Currently only support the WGS 1984 Geographic Projection (EPSG:4326).

        Args:
            proj_str(str): Well-Known-Text projection string.

        Raises:
            ValueError: unsupported projection systems.
        """  # noqa: E501
        # We don't support projected projections at this point
        if 'PROJCS' in proj_str:
            raise ValueError('Projected coordinate systems are not supported at this time. Please re-project '
                             'the shapefile to the WGS 1984 Geographic Projection (EPSG:4326).')
        # Only support the WGS 1984 geographic projection at this point
        elif 'GEOGCS' not in proj_str or 'WGS' not in proj_str or '1984' not in proj_str:
            raise ValueError('Only geographic projections are supported at this time. Please re-project shapefile to '
                             'the WGS 1984 Geographic Projection (EPSG:4326).')

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

        features = []

        for geometry in geojson_objs.geometries:
            properties = geometry.pop('properties', [])
            features.append({
                'type': 'Feature',
                'geometry': geometry,
                'properties': properties
            })

        geojson_objs = {
            'type': 'FeatureCollection',
            'features': features
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
        s_features = sorted(geojson['features'], key=lambda f: f['geometry']['coordinates'])

        for i, feature in enumerate(s_features):
            if 'geometry' not in feature or \
               'coordinates' not in feature['geometry'] or \
               'type' not in feature['geometry']:
                continue

            processed_feature = {
                'type': 'Feature',
                'geometry': {
                    'type': feature['geometry']['type'],
                    'coordinates': feature['geometry']['coordinates']
                },
                'properties': feature['properties'] if 'properties' in feature else {}
            }

            # Generate ID if not given
            if 'id' not in feature['properties']:
                feature['properties']['id'] = str(uuid.uuid4())

            post_processed_geojson['features'].append(processed_feature)

        return post_processed_geojson
