"""Operations relating to managing data folders on NUCAPT servers"""

import os
import shutil
from datetime import date

import yaml

import nucapt
from nucapt.exceptions import DatasetParseException
from nucapt.metadata import APTDataCollectionMetadata, GeneralMetadata

# Key variables
module_dir = os.path.dirname(os.path.abspath(nucapt.__file__))
template_path = os.path.join(module_dir, '..', 'template_directory')
data_path = os.path.join(module_dir, '..', 'working_directory')


class APTDataDirectory:
    """Class that represents a NUCAPT dataset"""

    def __init__(self, name, path, abstract, authors, dates, title):
        """Please use `load_dataset` instead

        :param name: str, name of dataset
        :param title: str, title of dataset
        :param authors: list, dicts describing authors
        :param abstract: str, abstract describing dataset
        :param dates: dict, 'creation' and 'publishing' date"""

        self.name = name
        self.path = path
        self.abstract = abstract
        self.authors = authors
        self.dates = dates
        self.title = title

    @classmethod
    def load_dataset_by_name(cls, name):
        """Load dataset by name. Assumes it is located in the proper place

        :param name: str, name of dataset
        :return: APTDataDirectory, APT dataset"""

        my_path = os.path.abspath(os.path.join(data_path, name))
        return APTDataDirectory.load_dataset_by_path(my_path)

    @classmethod
    def load_dataset_by_path(cls, path, name=None):
        """Read in dataset from directory

        :param path: str, Path to APT dataset
        :param name: str, Name of dataset. if not defined, inferred from path
        :return: APTDataDirectory, APT Dataset"""

        # Check if path does not exist
        if not os.path.isdir(path):
            raise DatasetParseException('No dataset at: ' + path)

        # Infer name, if need be
        if name is None:
            name = os.path.basename(path)

        # Read in the general metadata
        metadata_dir = os.path.join(path, 'General')
        metadata_file = os.path.join(metadata_dir, 'GeneralMetadata.yml')
        metadata = GeneralMetadata.from_yaml(metadata_file)
        is_valid, errors = metadata.validate_data()

        # Get the, now validated, metadata out of

        if len(errors) > 0:
            raise DatasetParseException(errors)
        return cls(name, path, metadata.metadata['abstract'], metadata['authors'],
                   metadata['dates'], metadata['title'])

    @staticmethod
    def initialize_dataset(title, abstract, authors):
        """Create a new dataset on the NUCAPT system

        :param title: str, title of dataset
        :param authors: list of dicts, author names.
            The dict should contain keys "first_name", "last_name", "affiliation"
        :return:
            str, name of dataset
            path, path to data
        """

        # Create a name for this dataset
        first_author = authors[0]["last_name"]
        index = 0
        while True:
            my_name = '%s_%s_%d'%(date.today().strftime("%d%b%y"), first_author, index)
            if not os.path.exists(os.path.join(data_path, my_name)):
                break
            index += 1

        # Copy the template directory to this path
        my_path = os.path.abspath(os.path.join(data_path, my_name))
        shutil.copytree(template_path, my_path)

        # Generate the dataset metadata
        my_metadata = dict(
            abstract=abstract,
            title=title,
            authors=authors,
            dates={'creation_date': date.today().strftime("%d%b%y")}
        )

        # Write to disk
        metadata_path = os.path.join(my_path, 'General', 'GeneralMetadata.yml')
        with open(metadata_path, 'w') as fp:
            yaml.dump(my_metadata, fp)

        return my_name, my_path

    def _get_collection_metadata_path(self):
        """Get path to APT collection method metadata

        :return: str, path
        """
        return os.path.join(self.path, 'DataCollection', 'CollectionMetadata.yaml')

    def update_collection_metadata(self, metadata):
        """Save metadata regarding the APT collection method to disk

        :param metadata: APTDataCollectionMetadata, metadata object
        :return: path to metadata"""

        metadata_path = self._get_collection_metadata_path()
        metadata.to_yaml(metadata_path)
        return metadata_path

    def load_collection_metadata(self):
        """Load in APT collection method metadata, if available

        :return: APTDataCollectionMetadata if present, else None"""

        if os.path.isfile(self._get_collection_metadata_path()):
            return APTDataCollectionMetadata.from_yaml(self._get_collection_metadata_path())
        return None
