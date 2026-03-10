"""
********************************************************************************
* Name: form_input_rws.py
* Author: glarsen, mlebaron
* Created On: October 17, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class FormInputRWS(ResourceWorkflowStep):
    """
    Workflow step that can be used to get form input from a user.

    Options:
        form_title(str): Title to be displayed at the top of the form. Defaults to the name of the step.
        status_label(str): Custom label for the status select form field. Defaults to "Status".
        param_class(dict): A param class to represent form fields.
        renderer(str): Renderer option. Available values are 'django' and 'bokeh'. Defauls to 'django'. 
        validators (dict, optional): A dictionary of validator functions to check parameter values
            before running the tool. Validators are called automatically when a parameter is set.
            The structure can be:
            
                {
                    'param_name': validator_func,            # Single parameter
                    ('param1', 'param2'): validator_func   # Multiple parameters
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

    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.workflow_views.FormInputWV'
    TYPE = 'form_input_resource_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'form_title': None,
            'status_label': None,
            'param_class': {},
            'renderer': 'django',
            'validators': {}
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

    def validate(self):
        super().validate()
        params = self._parameters
        form_values = params['form-values']['value']
        validators = self.options['validators']
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
