"""
********************************************************************************
* Name: xms_tool_rws.py
* Author: dgallup
* Created On: December, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class XMSToolRWS(ResourceWorkflowStep):
    """
    Workflow step that can be used to get XMSTool input from a user.

    Example argument mapping (provide options from the database, for input arguments):
    (Look in resource.datasets, where a dataset_type is a raster, for the dataset description, which is then filtered)
    'arg_mapping': {
        'input_raster': {
            'resource_attr': 'datasets',
            'filter_attr': 'dataset_type',
            'valid_values': ['RASTER_ASCII', 'RASTER_GEOTIFF'],
            'name_attr': 'description',
            'name_attr_regex': r'"(.*?[^\\])"',  # optional regex expression on the name_attr value
        },
    }

    Options:
        form_title(str): Title to be displayed at the top of the form. Defaults to the name of the step.
        status_label(str): Custom label for the status select form field. Defaults to "Status".
        xmstool_class(dict): xms tool class used on the form.
        arg_mapping(dict): dict of lookup options to map arguments to existing data.
        renderer(str): Renderer option. Available values are 'django' and 'bokeh'. Defauls to 'django'. 
    """  # noqa: #501

    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.workflow_views.XMSToolWV'
    TYPE = 'xms_tool_resource_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'form_title': None,
            'status_label': None,
            'xmstool_class': {},
            'arg_mapping': {},
            'renderer': 'django'
        })
        return default_options

    def init_parameters(self, *args, **kwargs):
        return {
            'form-values': {
                'help': 'Values from form',
                'value': {},
                'required': True
            },
            'resource_name': {
                'help': 'The name of the resource',
                'value': '',
                'required': True
            }
        }
