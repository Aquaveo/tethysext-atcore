"""
********************************************************************************
* Name: spatial_dataset_rws.py
* Author: nswain
* Created On: March 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import json
import pandas as pd
from tethysext.atcore.models.resource_workflow_steps import SpatialResourceWorkflowStep


class SpatialDatasetRWS(SpatialResourceWorkflowStep):
    """
    Workflow step used for setting dataset attributes on features.

    Options:
        geometry_source(varies): Geometry or parent to retrieve the geometry from. For passing geometry, use GeoJSON string.
        dataset_title(str): Title of the dataset (e.g.: Hydrograph). Defaults to 'Dataset'.
        template_dataset(pd.DataFrame): A Pandas dataset to use as a template for the dataset. Default is pd.DataFrame(columns=['X', 'Y'])
        read_only_columns(tuple,list): Names of columns of the template dataset that are read only. All columns are editable by default.
        plot_columns(Union[2-tuple, list of 2-tuple]): Two columns to plot. First column given will be plotted on the x axis, the second on the y axis. No plot if not given. Multiple series plotted if a list of 2-tuple given, ex: [(x1, y1), (x2, y2)].
        max_rows(integer): Maximum number of rows allowed in the dataset. No maximum if not given.
        empty_rows(integer): The number of empty rows to generate if an no/empty template dataset is given.
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialDatasetMWV'
    TYPE = 'spatial_dataset_workflow_step'

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
            'geometry_source': None,
            'dataset_title': self.DEFAULT_DATASET_TITLE,
            'template_dataset': self.DEFAULT_DATASET,
            'read_only_columns': [],
            'plot_columns': [],
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

    def to_dict(self):
        """
        Serialize ResourceWorkflowStep into a dictionary.

        Returns:
            dict: dictionary representation of ResourceWorkflowStep.
        """
        # Get default dict representation
        d = super().to_dict()

        # serialize the dataframe parameters
        datasets = {}

        if d['parameters']['datasets']:
            for feature_id, dataframe in d['parameters']['datasets'].items():
                datasets.update({feature_id: dataframe.to_dict(orient='list')})

        d['parameters']['datasets'] = datasets

        return d

    def to_geojson(self, as_str=False):
        """
        Serialize SpatialResourceWorkflowStep to GeoJSON.

        Args:
            as_str(bool): Returns GeoJSON string if True, otherwise returns dict equivalent.

        Returns:
            str or dict: GeoJSON string or dict equivalent representation of the spatial portions of a SpatialResourceWorkflowStep.
        """  # noqa: E501
        # Get geometry from parent step
        geojson_dict = self.resolve_option('geometry_source')

        # Serialize dataset parameters and map as a property to each feature in the GeoJSON
        serlialized_step = self.to_dict()
        serialized_datasets = serlialized_step['parameters']['datasets']

        for feature in geojson_dict['features']:
            feature_id = str(feature['properties']['id'])
            if feature_id in serialized_datasets:
                feature['properties'].pop('dataset', None)
                dataset_title = self.options.get('dataset_title', 'dataset')
                dataset_codename = dataset_title.lower().replace(' ', '_')

                # Add some metadata to the dataset object
                dataset = serialized_datasets[feature_id]
                columns = self.options.get('template_dataset').columns.to_list()
                length = len(dataset[columns[0]])

                dataset['meta'] = {
                    'columns': columns,
                    'length': length,
                }

                # Add dataset as property of geojson feature
                feature['properties'][dataset_codename] = {
                    'type': 'dataset',
                    'value': dataset
                }

        if as_str:
            return json.dumps(geojson_dict)

        return geojson_dict
