"""
********************************************************************************
* Name: set_status_rws.py
* Author: nswain
* Created On: August 19, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class SetStatusRWS(ResourceWorkflowStep):
    """
    Workflow step that can be used to change the status of a workflow with the click of a button.
    
    Options:
        form_title(str): Title to be displayed at the top of the form. Defaults to the name of the step.
        status_label(str): Custom label for the status select form field. Defaults to "Status".
        statuses(list<dicts<status,label>>): List of dictionaries with two keys: "status" and "label". The value of "status" must be a valid status from the StatusMixin as determined by the valid_statuses() method on the step. The value of the "label" will be what is displayed to the user. If "label" is None or not given, the value of "status" will be displayed to the user.
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.workflow_views.SetStatusWV'
    TYPE = 'set_status_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        return {
            'form_title': None,
            'status_label': None,
            'statuses': [
                {'status': SetStatusRWS.STATUS_COMPLETE,
                 'label': None}
            ],
        }

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Returns:
            dict<name:dict<help,value,required>>: Dictionary of all parameters with their initial value set.
        """
        return {
            'comments': {
                'help': 'Comments on reason for changing status to this status.',
                'value': '',

                'required': False
            },
        }

    def validate(self):
        """
        Validates parameter values of this this step.

        Returns:
            bool: True if data is valid, else Raise exception.

        Raises:
            ValueError
        """
        # Run super validate method first to perform built-in checks (e.g.: Required)
        super().validate()

    def validate_statuses(self):
        """
        Validate the status dictionaries given in the "statuses" option.

        Raises:
            RuntimeError: Invalid statuses or malformed status dictionaries.
        """
        valid_statuses = self.valid_statuses()

        # Validate the statuses
        for status_dict in self.options.get('statuses', []):
            if 'status' not in status_dict.keys():
                raise RuntimeError(f'Key "status" not found in status dict provided by option '
                                   f'"statuses": {status_dict}')

            status = status_dict['status']
            if status_dict['status'] not in valid_statuses:
                raise RuntimeError(f'Status "{status}" is not a valid status for {self.__class__.__name__}. '
                                   f'Must be one of: {", ".join(valid_statuses)}')
