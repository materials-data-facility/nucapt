"""Operations relating to managing data folders on NUCAPT servers"""

import os
from abc import abstractmethod, ABCMeta
from datetime import date

import nucapt
from nucapt.exceptions import DatasetParseException
from nucapt.metadata import APTDataCollectionMetadata, GeneralMetadata, APTSampleGeneralMetadata

# Key variables
module_dir = os.path.dirname(os.path.abspath(nucapt.__file__))
template_path = os.path.join(module_dir, '..', 'template_directory')
data_path = os.path.join(module_dir, '..', 'working_directory')


class DataDirectory(metaclass=ABCMeta):
    """Class to represent a set of data stored on this server"""
    def __init__(self, name, path):
        self.name = name
        self.path = os.path.abspath(path)

    @classmethod
    @abstractmethod
    def load_dataset_by_path(cls, path):
        """Read in dataset from directory

        :param path: str, Path to APT dataset
        :param name: str, Name of dataset. if not defined, inferred from path
        :return: APTDataDirectory, APT Dataset"""
        pass


class APTDataDirectory(DataDirectory):
    """Class that represents a NUCAPT dataset"""

    def __init__(self, name, path, abstract, authors, dates, title):
        """Please use `load_dataset` instead

        :param name: str, name of dataset
        :param title: str, title of dataset
        :param authors: list, dicts describing authors
        :param abstract: str, abstract describing dataset
        :param dates: dict, 'creation' and 'publishing' date"""
        super(APTDataDirectory, self).__init__(name, path)
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
    def load_dataset_by_path(cls, path):
        """Read in dataset from directory

        :param path: str, Path to APT dataset
        :return: APTDataDirectory, APT Dataset"""

        # Check if path does not exist
        if not os.path.isdir(path):
            raise DatasetParseException('No dataset at: ' + path)

        # Infer name
        name = os.path.basename(path)

        # Read in the general metadata
        metadata_file = os.path.join(path, 'GeneralMetadata.yml')
        metadata = GeneralMetadata.from_yaml(metadata_file)
        is_valid, errors = metadata.validate_data()

        # Get the, now validated, metadata out of the object and instantiate the data
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
        :param abstract: str, abstract describing this dataset
        :return:
            str, name of dataset
            path, path to data
        """

        # Create a name for this dataset
        first_author = authors[0]["last_name"]
        index = 0
        while True:
            my_name = '%s_%s_%d' % (date.today().strftime("%d%b%y"), first_author, index)
            if not os.path.exists(os.path.join(data_path, my_name)):
                break
            index += 1

        # Make a new directory for this dataset
        my_path = os.path.abspath(os.path.join(data_path, my_name))
        os.makedirs(my_path)

        # Generate the dataset metadata
        my_metadata = GeneralMetadata(
            abstract=abstract,
            title=title,
            authors=authors,
            dates={'creation_date': date.today().strftime("%d%b%y")}
        )

        # Write to disk
        metadata_path = os.path.join(my_path, 'GeneralMetadata.yml')
        my_metadata.to_yaml(metadata_path)

        return my_name, my_path

    @classmethod
    def get_all_datasets(cls, path=data_path):
        """Load all available datasets in at a certain path

        :param path: str, path to investigate
        :return: dict
            key: String, path name
            value: `APTDataDirectory` if metadata file is valid, `DatasetParseException` otherwise"""

        output = dict()
        for sub_path in os.listdir(path):
            if not os.path.isdir(os.path.join(path, sub_path)):
                continue

            # Get "name" of directory
            try:
                output[sub_path] = cls.load_dataset_by_path(os.path.join(path, sub_path))
            except DatasetParseException as err:
                output[sub_path] = err
            except:
                continue
        return output


class APTSampleDirectory(DataDirectory):
    """Holds data associated with a certain sample"""

    def __init__(self, dataset_name, sample_name, path):
        """Do not use. Use `load_dataset_by_path` or `load_dataset_by_name`"""
        super(APTSampleDirectory, self).__init__('%s_%s'%(dataset_name, sample_name), path)
        self.dataset_name = dataset_name
        self.sample_name = sample_name

    @classmethod
    def load_dataset_by_path(cls, path):
        # Check that the path exists
        if not os.path.isdir(path):
            raise DatasetParseException('No such path: ' + path)

        # Get the names
        words = os.path.split(path)
        sample_name = words[-1]
        dataset_name = words[-2]
        return cls(dataset_name, sample_name, path)

    @classmethod
    def load_dataset_by_name(cls, dataset_name, sample_name):
        """Load a sample by name

        :param dataset_name: str, name of dataset containing sample
        :param sample_name: str, name of sample
        :return: APTSampleDirectory, desired sample
        """

        path = os.path.join(data_path, dataset_name, sample_name)
        return APTSampleDirectory.load_dataset_by_path(path)

    @classmethod
    def create_sample(cls, dataset_name, form):
        """Generate a new sample given HTML form data

        :param dataset_name: str, Name of dataset that will contain this new sample
        :param form: LEAPSanmpleForm, user request
        :return: str, sample name
        """

        # Parse the metadata
        general = APTSampleGeneralMetadata.from_form(form.sample_form)
        collection = APTDataCollectionMetadata.from_form(form.collection_form)

        # Create a directory and save metadata in it
        sample_name = general['sample_name']
        path = os.path.join(data_path, dataset_name, sample_name)

        #   Check if that path exists
        if os.path.isdir(path):
            raise DatasetParseException('Sample %s already exists for dataset %s'%(sample_name, dataset_name))
        os.mkdir(path)

        general.to_yaml(os.path.join(path, 'SampleInformation.yaml'))
        collection.to_yaml(os.path.join(path, 'CollectionMethod.yaml'))

        # Download the files
        # TBD

        return sample_name

    def _get_sample_information_path(self):
        """Get path to APT sample information

        :return: str, path
        """
        return os.path.join(self.path, 'SampleInformation.yaml')

    def update_sample_information(self, metadata):
        """Save sample information to disk

        :param metadata: APTSampleGeneralMetadata, metadata object
        :return: path to metadata"""

        metadata_path = self._get_sample_information_path()
        metadata.to_yaml(metadata_path)
        return metadata_path

    def load_sample_information(self):
        """Load in APT collection method metadata, if available

        :return: APTDataCollectionMetadata if present, else None"""

        if os.path.isfile(self._get_sample_information_path()):
            return APTSampleGeneralMetadata.from_yaml(self._get_sample_information_path())
        return None

    def _get_collection_metadata_path(self):
        """Get path to APT collection method metadata

        :return: str, path
        """
        return os.path.join(self.path, 'CollectionMetadata.yaml')

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
