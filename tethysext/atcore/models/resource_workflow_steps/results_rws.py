"""
********************************************************************************
* Name: results_rws.py
* Author: nswain
* Created On: March 28, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from sqlalchemy.orm import relationship
from tethysext.atcore.mixins import ResultsMixin, AttributesMixin
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from tethysext.atcore.models.app_users.associations import step_result_association


class ResultsResourceWorkflowStep(ResourceWorkflowStep, AttributesMixin, ResultsMixin):
    """
    Abstract base class of all Results Resource Workflow Steps.
    """  # noqa: E501
    TYPE = 'results_resource_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    results = relationship(
        'ResourceWorkflowResult',
        secondary=step_result_association,
        order_by='ResourceWorkflowResult.order',
        cascade='all,delete',
        backref='steps'
    )

    @property
    def default_options(self):
        """
        Returns default options dictionary for the result.
        """
        default_options = super().default_options
        return default_options

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.
        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return {}

    def reset(self):
        """
        Resets the step back to its initial state.
        """
        for result in self.results:
            result.reset()

        super().reset()
