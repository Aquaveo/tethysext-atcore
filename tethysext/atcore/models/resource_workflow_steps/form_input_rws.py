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
        }
