"""
********************************************************************************
* Name: table_input_rws.py
* Author: nswain
* Created On: March 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import pandas as pd
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class TableInputRWS(ResourceWorkflowStep):
    """
    Workflow step used for setting table of data.

    Options:
        dataset_title(str): Title of the dataset (e.g.: Hydrograph). Defaults to 'Dataset'.
        template_dataset(pd.DataFrame): A Pandas dataset to use as a template for the dataset. Default is pd.DataFrame(columns=['X', 'Y'])
        read_only_columns(tuple,list): Names of columns of the template dataset that are read only. All columns are editable by default.
        plot_columns(Union[2-tuple, list of 2-tuple]): Two columns to plot. First column given will be plotted on the x axis, the second on the y axis. No plot if not given. Multiple series plotted if a list of 2-tuple given, ex: [(x1, y1), (x2, y2)].
        max_rows(integer): Maximum number of rows allowed in the dataset. No maximum if not given.
        empty_rows(integer): The number of empty rows to generate if an no/empty template dataset is given.
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.workflow_views.table_input_wv.TableInputWV'

    TYPE = 'table_input_rws'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    DEFAULT_DATASET_TITLE = 'Dataset'
    DEFAULT_EMPTY_ROWS = 10
    DEFAULT_MAX_ROWS = 1000
    DEFAULT_COLUMNS = ['X', 'Y']
    DEFAULT_DATASET = pd.DataFrame(columns=DEFAULT_COLUMNS)

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'dataset_title': self.DEFAULT_DATASET_TITLE,
            'template_dataset': self.DEFAULT_DATASET,
            'read_only_columns': [],
            'plot_columns': [],
            'optional_columns': [],
            'max_rows': self.DEFAULT_MAX_ROWS,
            'empty_rows': self.DEFAULT_EMPTY_ROWS
        })
        return default_options

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Returns:
            dict<name:dict<help,value,required>>: Dictionary of all parameters with their initial value set.
        """
        return {
            'dataset': {
                'help': 'Valid JSON representing datasets input by user.',
                'value': None,
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
        dataset = self.get_parameter('dataset')
        dataset_title = self.options.get('dataset_title', self.DEFAULT_DATASET_TITLE)
        if not dataset:
            raise ValueError(f'Please fill in the {dataset_title} to continue.')
        return True
