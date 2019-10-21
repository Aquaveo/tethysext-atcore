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
        param_class(dict): A param class to represent form fields
    """  # noqa: #501

    def init_parameters(self, *args, **kwargs):
        return {
            'form-values': {
                'help': 'Values from form',
                'value': {},
                'required': True
            },
        }

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
            'param_class': {}
        })
        return default_options

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        super().__init__(*args, **kwargs)

    # def validate_statuses(self):
    #     """
    #     Validate the status dictionaries given in the "statuses" option.
    #
    #     Raises:
    #         RuntimeError: Invalid statuses or malformed status dictionaries.
    #     """
    #     # valid_statuses = self.valid_statuses()
    #
    #     # Validate the statuses
    #     # for status_dict in self.options.get('statuses', []):
    #     #     if 'status' not in status_dict.keys():
    #     #         raise RuntimeError(f'Key "status" not found in status dict provided by option '
    #     #                            f'"statuses": {status_dict}')
    #     #
    #     #     status = status_dict['status']
    #     #     if status not in valid_statuses:
    #     #         raise RuntimeError(f'Status "{status}" is not a valid status for {self.__class__.__name__}. '
    #     #                            f'Must be one of: {", ".join(valid_statuses)}')
