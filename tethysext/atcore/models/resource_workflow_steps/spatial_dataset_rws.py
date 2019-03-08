"""
********************************************************************************
* Name: spatial_dataset_rws.py
* Author: nswain
* Created On: March 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import pandas as pd
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS


class SpatialDatasetRWS(SpatialInputRWS):
    """
    Workflow step used for setting dataset attributes on features.

    Options:
        geometry_source(varies): Geometry or parent to retrieve the geometry from. For passing geometry, use GeoJSON string.
        dataset_title(str): Title of the dataset (e.g.: Hydrograph). Defaults to 'Dataset'.
        template_dataset(pd.DataFrame): A Pandas dataset to use as a template for the dataset. Default is pd.DataFrame(columns=['X', 'Y'])
        read_only_columns(tuple,list): Names of columns of the template dataset that are read only. All columns are editable by default.
        plot_columns(2-tuple): Two columns to plot. First column given will be plotted on the x axis, the second on the y axis. No plot if not given.
        max_rows(integer): Maximum number of rows allowed in the dataset. No maximum if not given.
        empty_rows(integer): The number of empty rows to generate if an no/empty template dataset is given.
    """  # noqa: #501
    TYPE = 'spatial_dataset_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    DEFAULT_DATASET_TITLE = 'Dataset'
    DEFAULT_EMPTY_ROWS = 10
    DEFAULT_MAX_ROWS = 1000
    DEFAULT_COLUMNS = ['X', 'Y']
    DEFAULT_DATASET = pd.DataFrame(columns=DEFAULT_COLUMNS)

    def __init__(self, geoserver_name, map_manager, spatial_manager, *args, **kwargs):
        """
        Constructor.

        Args:
            geoserver_name(str): Name of geoserver setting to use.
            map_manager(MapManager): Instance of MapManager to use for the map view.
            spatial_manager(SpatialManager): Instance of SpatialManager to use for the map view.
        """
        super().__init__(
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            *args, **kwargs
        )
        self.controller_path = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialDatasetMWV'

    @property
    def default_options(self):
        return {
            'geometry_source': None,
            'dataset_title': self.DEFAULT_DATASET_TITLE,
            'template_dataset': self.DEFAULT_DATASET,
            'read_only_columns': [],
            'plot_columns': [],
            'max_rows': self.DEFAULT_MAX_ROWS,
            'empty_rows': self.DEFAULT_EMPTY_ROWS
        }

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Returns:
            dict<name:dict<help,value,required>>: Dictionary of all parameters with their initial value set.
        """
        return {
            'datasets': {
                'help': 'Valid JSON representing geometry input by user.',
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
        # Run super validate method first to perform built-in checks (e.g.: Required)
        super().validate()

        geometry = self.resolve_option('geometry_source')
        datasets = self.get_parameter('datasets')
        dataset_title = self.options.get('dataset_title', self.DEFAULT_DATASET_TITLE)

        # Validate that there is one dataset for each feature
        if geometry and 'features' in geometry:
            for feature in geometry['features']:
                if 'properties' not in feature or 'id' not in feature['properties']:
                    continue

                feature_id = str(feature['properties']['id'])

                # Verify that there is an entry in datasets parameter corresponding
                # to the feature_id and it is not empty
                if datasets is None or feature_id not in datasets or \
                        datasets[feature_id] is None or datasets[feature_id].empty:
                    raise ValueError('At least one {0} is empty. You must define one {0} for each feature to continue.'
                                     .format(dataset_title))
