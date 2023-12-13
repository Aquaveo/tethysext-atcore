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
        * **form_title** (``str``): Title to be displayed at the top of the form. Defaults to the name of the step.
        * **status_label** (``str``): Custom label for the status select form field. Defaults to "Status".
        * **param_class** (``dict``): A param class to represent form fields.
        * **renderer** (``str``): Renderer option. Available values are 'django' and 'bokeh'. Defauls to 'django'.

    **Parameters**:
        * **form-values** (``dict``): Values from form where keys are then names of the fields.
        * **resource_name** (``str``): The name of the resource.

    **Examples**:

        *flow_options.py*:

        .. code-block:: python

            import param

            class FlowOptions(param.Parameterized):
                storm_type = param.ListSelector(
                    label='Design Storm Scenario',
                    doc='Select one or more scenarios to run for this analysis.',
                    default='option1',
                    objects=['option1', 'option2', 'option3'],
                    allow_None=False
                )

        *workflow.py*:

        .. code-block:: python

            step = FormInputRWS(
                name='Select Flow Simulation Options',
                order=20,
                help='Select options for the flow computation.',
                options={
                    'param_class': 'flow_options.FlowOptions',
                    'form_title': 'Flow Run Options',
                    'renderer': 'django'
                }
            )

    **Example Parameters**:

        .. code-block:: python

            >>> step.get_parameter('form-values')
            {
                'storm_type': ['option1', 'option2'],
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
