"""
********************************************************************************
* Name: xms_tool_rws.py
* Author: dgallup, ysun
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
        validators (dict, optional): A dictionary of validator functions to check parameter values
            before running the tool. Validators are called automatically when a parameter is set.
            The structure can be:
            
                {
                    'param_name': validator_func,            # Single parameter
                    ('param_name_1', 'param_name_2'): validator_func   # Multiple parameters
                }

            Where `validator_func` is a callable that receives the parameter value(s) and raises a `ValueError`
            if the value is invalid.

            Examples:

                # Validate a single parameter
                def validate_start(value):
                    if value < 0:
                        raise ValueError("Start value must be non-negative")

                validators = {
                    'start_time': validate_start
                }

                # Validate multiple parameters together
                def validate_range(start, end):
                    if start >= end:
                        raise ValueError("Start must be earlier than end")

                validators = {
                    ('start_time', 'end_time'): validate_range
                }
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
            'renderer': 'django',
            'validators': {}
        })
        return default_options

    def init_parameters(self, *args, **kwargs):
        return {
            'form-values': {
                'help': 'Values from form',
                'value': {},
                'required': True,
                'is_tabular': True,
            },
            'resource_name': {
                'help': 'The name of the resource',
                'value': '',
                'required': True
            }
        }

    def validate(self):
        super().validate()
        form_values = self._parameters['form-values']['value']['value']
        validators = self.options.get('validators', {})
        for param, validator in validators.items():
            if isinstance(param, str):
                param = (param,)

            values = []
            for p in param:
                if p not in form_values:
                    raise ValueError(f'Missing required parameter: {p}')
                values.append(form_values[p])

            try:
                validator(*values)
            except ValueError as e:
                raise ValueError(f'Invalid parameter {param}: {str(e)}')
        return True
