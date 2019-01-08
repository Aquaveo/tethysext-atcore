"""
********************************************************************************
* Name: map_workflow_view.py
* Author: nswain
* Created On: November 21, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
import os
import zipfile
import uuid
import shutil
import logging
import shapefile as shp
import geojson
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.shortcuts import redirect, reverse
from django.contrib import messages
from tethys_sdk.gizmos import MVDraw
from tethys_apps.utilities import get_active_app
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.models.app_users.resource_workflow_steps import SpatialInputResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows.base import AppUsersResourceWorkflowController
from tethysext.atcore.controllers.map_view import MapView


log = logging.getLogger(__name__)


class MapWorkflowView(MapView, AppUsersResourceWorkflowController):
    """
    Controller for a map view with workflows integration.
    """
    template_name = 'atcore/resource_workflows/map_workflow_view.html'

    def get_context(self, request, context, model_db, map_manager, workflow_id, step_id, *args, **kwargs):
        """
        Get workflow and steps and add to the context.

        Args:
            request (HttpRequest): The request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        _ResourceWorkflow = self.get_resource_workflow_model()
        session = None

        try:
            make_session = self.get_sessionmaker()
            session = make_session()
            workflow = self.get_workflow(request, workflow_id, session=session)
            current_step = self.get_step(request, step_id=step_id, session=session)
            previous_step, next_step = workflow.get_adjacent_steps(current_step)

            # Initialize drawing tools for spatial input parameter types.
            if not isinstance(current_step, SpatialInputResourceWorkflowStep):
                raise TypeError('Invalid step type for view: {}. Must be a SpatialInputResourceWorkflowStep.'.format(
                    type(current_step))
                )

            # Get Map View
            map_view = context['map_view']

            # Disable feature selection on all layers so it doesn't interfere with drawing
            for layer in map_view.layers:
                layer.feature_selection = False
                layer.editable = False

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
                output_format='GeoJSON'
            )

            if draw_options is not None and 'map_view' in context:
                map_view.draw = draw_options

            # Save changes to map view
            context.update({'map_view': map_view})

            # Build step cards
            previous_status = None
            steps = []

            for workflow_step in workflow.steps:
                status = workflow_step.get_status(workflow_step.ROOT_STATUS_KEY).lower()
                steps.append({
                    'id': workflow_step.id,
                    'help': workflow_step.help,
                    'name': workflow_step.name,
                    'type': workflow_step.type,
                    'status': status,
                    'link': previous_status == current_step.STATUS_COMPLETE or previous_status is None,

                })

                previous_status = status

            # Get the current app
            active_app = get_active_app(request)

            context.update({
                'workflow': workflow,
                'steps': steps,
                'current_step': current_step,
                'previous_step': previous_step,
                'next_step': next_step,
                'url_map_name': '{}:{}_workflow_step'.format(active_app.namespace, workflow.type),
                'map_title': workflow.name,
                'map_subtitle': workflow.DISPLAY_TYPE_SINGULAR,
                'allow_shapefile': current_step.options['allow_shapefile']
            })

        except (StatementError, NoResultFound):
            messages.warning(request, 'The {} could not be found.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(self.back_url)
        finally:
            session and session.close()

        return context

    def save_step_data(self, request, resource_id, workflow_id, step_id, back_url, *args, **kwargs):
        """
        Handle POST requests with method save-step-data.
        Args:
            request(HttpRequest): The request.
            resource_id(str): ID of the resource this workflow applies to.
            workflow_id(str): ID of the workflow.
            step_id(str): ID of the step to render.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        _ResourceWorkflow = self.get_resource_workflow_model()
        session = None

        try:
            # Prepare POST parameters
            geometry = request.POST.get('geometry', None)
            shapefile = request.FILES.get('shapefile', None)

            make_session = self.get_sessionmaker()
            session = make_session()
            workflow = self.get_workflow(request, workflow_id, session=session)
            current_step = self.get_step(request, step_id=step_id, session=session)
            _, next_step = workflow.get_adjacent_steps(current_step)

            if not geometry and not shapefile:
                current_step.set_parameter('geometry', None)
                session.commit()
                raise ValueError('You must either draw at least one shape or upload a shapefile.')

            # Handle File parameter
            shapefile_geojson = self.parse_shapefile(request, shapefile)

            # Handle geometry parameter
            geometry_geojson = self.parse_geometry(geometry)

            # Combine the geojson objects.
            combined_geojson = self.combine_geojson_objects(shapefile_geojson, geometry_geojson)
            current_step.set_parameter('geometry', combined_geojson)

            # Validate the Parameters
            current_step.validate()

            session.commit()

            # Go to next step
            active_app = get_active_app(request)
            step_url = '{}:{}_workflow_step'.format(active_app.namespace, workflow.type)

            # If shapefile is given, reload current step to show user the features loaded from the shapefile
            if shapefile:
                response = redirect(reverse(step_url, args=(resource_id, workflow_id, str(current_step.id))))

            # Otherwise, go to the next step
            else:
                response = redirect(reverse(step_url, args=(resource_id, workflow_id, str(next_step.id))))

        except (StatementError, NoResultFound):
            messages.warning(request, 'The {} could not be found.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            response = redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            response = redirect(self.back_url)

        except ValueError as e:
            session and session.rollback()
            messages.error(request, e)
            return self.get(request, resource_id=resource_id, workflow_id=workflow_id, step_id=step_id)
        except RuntimeError as e:
            session and session.rollback()
            messages.error(request, "We're sorry, an unexpected error has occurred.")
            log.exception(e)
            return self.get(request, resource_id=resource_id, workflow_id=workflow_id, step_id=step_id)
        finally:
            session and session.close()

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

    def parse_geometry(self, geometry):
        """
        Parse the geometry into GeoJSON and validate.

        Args:
            request(HttpRequest): The request.
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

    def combine_geojson_objects(self, shapefile_geojson, geometry_geojson):
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
