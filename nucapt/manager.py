"""Operations relating to managing data folders on NUCAPT servers"""

import os
from abc import abstractmethod, ABCMeta
from datetime import date
from glob import glob

import nucapt
from nucapt.exceptions import DatasetParseException
from nucapt.metadata import APTDataCollectionMetadata, GeneralMetadata, APTSampleGeneralMetadata, \
    APTReconstructionMetadata

# Key variables
module_dir = os.path.dirname(os.path.abspath(nucapt.__file__))
template_path = os.path.join(module_dir, '..', 'template_directory')
data_path = os.path.join(module_dir, '..', 'working_directory')


class DataDirectory(metaclass=ABCMeta):
    """Class to represent a set of data stored on this server"""
    def __init__(self, name, path):
        if not os.path.isdir(path):
            raise DatasetParseException('No such path: ' + path)
        self.name = name
        self.path = os.path.abspath(path)

    @classmethod
    @abstractmethod
    def load_dataset_by_path(cls, path):
        """Read in dataset from directory

        :param path: str, Path to APT dataset
        :return: DataDirectory"""
        pass


class APTDataDirectory(DataDirectory):
    """Class that represents a NUCAPT dataset"""

    def __init__(self, name, path):
        """Please use `load_dataset` instead

        :param name: str, name of dataset
        :param path: str, path to dataset"""
        super(APTDataDirectory, self).__init__(name, path)

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
        name = os.path.basename(path)
        return cls(name, path)

    @classmethod
    def initialize_dataset(cls, form):
        """Create a new dataset

        :param form: CreateForm, Form describing sample
        :return:
            str, name of dataset
            path, path to data
        """

        # Create a name for this dataset
        metadata = GeneralMetadata.from_form(form)
        first_author = metadata['authors'][0]['last_name']
        index = 0
        while True:
            my_name = '%s_%s_%d' % (date.today().strftime("%d%b%y"), first_author, index)
            if not os.path.exists(os.path.join(data_path, my_name)):
                break
            index += 1

        # Make a new directory for this dataset
        my_path = os.path.abspath(os.path.join(data_path, my_name))
        os.makedirs(my_path)

        # Initialize this dataset
        dataset = cls(my_name, my_path)

        # Add start date
        metadata.metadata['dates'] = {'creation_date': date.today().strftime("%d%b%y")}

        # Write to disk
        metadata_path = dataset._get_metadata_path()
        metadata.to_yaml(metadata_path)

        return dataset

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

    def _get_metadata_path(self):
        """Get the path to the generaml metadata about this dataset

        :return: str, path to metadata file
        """

        return os.path.join(self.path, 'GeneralMetadata.yaml')

    def get_metadata(self):
        """Get the general metadata for this dataset

        :return: GeneralMetadata, metadata for this dataset
        """

        return GeneralMetadata.from_yaml(self._get_metadata_path())

    def update_metadata(self, form):
        """Update the metadata for this dataset

        :param form: CreateForm, Form to generate"""

        current_metadata = self.get_metadata()
        new_metadata = GeneralMetadata.from_form(form)
        current_metadata.metadata.update(new_metadata.metadata)
        current_metadata.to_yaml(self._get_metadata_path())

    def list_samples(self):
        """Get the list of samples for this dataset

        :return:
            - list of APTSampleDirectory, names of samples
            - errors: List of errors """

        # Find all subdirectories that contain "SampleInformation.yaml"
        output = []
        errors = []
        for file in glob("%s/*/SampleInformation.yaml" % self.path):
            try:
                output.append(APTSampleDirectory.load_dataset_by_path(os.path.dirname(file)))
            except DatasetParseException as exc:
                errors.extend(exc.errors)
        return output, errors


class APTSampleDirectory(DataDirectory):
    """Holds data associated with a certain sample"""

    def __init__(self, dataset_name, sample_name, path):
        """Do not use. Use `load_dataset_by_path` or `load_dataset_by_name`"""
        super(APTSampleDirectory, self).__init__('%s_%s'%(dataset_name, sample_name), path)
        self.dataset_name = dataset_name
        self.sample_name = sample_name

    @classmethod
    def load_dataset_by_path(cls, path):
        # Get the names
        temp_path, sample_name = os.path.split(path)
        temp_path, dataset_name = os.path.split(temp_path)
        return cls(dataset_name, sample_name, path)

    @classmethod
    def load_dataset_by_name(cls, dataset_name, sample_name):
        """Load a sample by name

        :param dataset_name: str, name of dataset containing sample
        :param sample_name: str, name of sample
        :return: APTSampleDirectory, desired sample
        """

        path = os.path.join(data_path, dataset_name, sample_name)
        return cls.load_dataset_by_path(path)

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
        sample_name = form.sample_name.data
        path = os.path.join(data_path, dataset_name, sample_name)

        #   Check if that path exists
        if os.path.isdir(path):
            raise DatasetParseException('Sample %s already exists for dataset %s'%(sample_name, dataset_name))
        os.mkdir(path)

        # Instantiate the object
        sample = cls(dataset_name, sample_name, path)

        general.to_yaml(sample._get_sample_information_path())
        collection.to_yaml(sample._get_collection_metadata_path())

        return sample_name

    def _get_sample_information_path(self):
        """Get path to APT sample information

        :return: str, path
        """
        return os.path.join(self.path, 'SampleInformation.yaml')

    def update_sample_information(self, form):
        """Save sample information to disk

        :param form: APTSampleDescriptionForm, metadata object
        :return: path to metadata"""

        # Validate the form
        metadata = APTSampleGeneralMetadata.from_form(form)

        # Save it
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
        return os.path.join(self.path, 'CollectionMethod.yaml')

    def update_collection_metadata(self, form):
        """Save metadata regarding the APT collection method to disk

        :param metadata: APTDataCollectionMetadata, metadata object
        :return: path to metadata"""

        metadata = APTDataCollectionMetadata.from_form(form)

        metadata_path = self._get_collection_metadata_path()
        metadata.to_yaml(metadata_path)
        return metadata_path

    def load_collection_metadata(self):
        """Load in APT collection method metadata, if available

        :return: APTDataCollectionMetadata if present, else None"""

        if os.path.isfile(self._get_collection_metadata_path()):
            return APTDataCollectionMetadata.from_yaml(self._get_collection_metadata_path())
        return None

    def get_rhit_path(self):
        """Get the path to the RHIT file

        :return: str, RHIT path"""

        # Find the *RHIT file in this directory
        file = glob(os.path.join(self.path, '*.RHIT'))
        if len(file) > 1:
            raise DatasetParseException('More than 1 RHIT file! Should be exactly one')

        return os.path.join(self.path, file[0])

    def list_reconstructions(self):
        """Get all reconstructions for this sample

        :return:
            - list of APTSampleDirectory, reconstructions
            - list of str, errors"""

        # Find all subdirectories that contain "SampleInformation.yaml"
        managers = []
        metadata = []
        errors = []
        for file in glob("%s/*/ReconstructionMetadata.yaml" % self.path):
            dirname = os.path.dirname(file)
            recon_name = os.path.basename(dirname)
            try:
                managers.append(APTReconstruction.load_dataset_by_path(os.path.dirname(file)))
                try:
                    metadata.append(managers[-1].load_metadata())
                except DatasetParseException as exc:
                    metadata.append({})
                    errors.extend(["%s:%s"%(recon_name, x) for x in exc.errors])
            except DatasetParseException as exc:
                errors.extend(["%s:%s"%(recon_name, x) for x in exc.errors])
        return managers, metadata, errors


class APTReconstruction(DataDirectory):
    """Directory describing a reconstruction"""

    def __init__(self, dataset_name, sample_name, recon_name, path):
        """Do not use, use `load_by_name` or `load_by_path` instead"""
        super(APTReconstruction, self).__init__(self._make_name(dataset_name, sample_name, recon_name), path)
        self.dataset_name = dataset_name
        self.sample_name = sample_name
        self.recon_name = recon_name

    @staticmethod
    def _make_name(dataset, sample, recon):
        return '_'.join([dataset, sample, recon])

    @classmethod
    def create_reconstruction(cls, form, dataset_name, sample_name):
        """Add a new construction to a sample

        :param form: AddReconstructionForm, Form from web service
        :param
        :return: str, Reconstruction name
        """

        # Get the recon_name
        recon_name = form.data['name']

        # Validate metadata
        form_data = dict(form.data)
        del form_data['name']
        del form_data['pos_file']
        metadata = APTReconstructionMetadata(**form_data)

        # Make the directory and save the metadata
        path = cls._make_path(dataset_name, sample_name, recon_name)
        if os.path.isdir(path):
            raise DatasetParseException('Recon %s already exists' % (recon_name))
        os.mkdir(path)
        recon = cls.load_dataset_by_path(path)

        metadata.to_yaml(recon._get_metadata_path())

        return recon_name

    @classmethod
    def load_dataset_by_path(cls, path):
        temp_path, recon_name = os.path.split(path)
        temp_path, sample_name = os.path.split(temp_path)
        temp_path, dataset_name = os.path.split(temp_path)
        return cls(dataset_name, sample_name, recon_name, path)

    @classmethod
    def load_dataset_by_name(cls, dataset_name, sample_name, recon_name):
        """Load an APT reconstruction by name

        :param dataset_name: str, name of dataset
        :param sample_name: str, name of sample
        :param recon_name: str, name of reconstruction
        :return: APTReconstruction
        """

        path = cls._make_path(dataset_name, sample_name, recon_name)
        return cls(dataset_name, sample_name, recon_name, path)

    @classmethod
    def _make_path(cls, dataset_name, sample_name, recon_name):
        return os.path.join(data_path, dataset_name, sample_name, recon_name)

    def _get_metadata_path(self):
        """Get the path to the metadata file"""
        return os.path.join(self.path, 'ReconstructionMetadata.yaml')

    def load_metadata(self):
        """Load in the metadata

        :return: APTReconstructionMetadata
        """

        return APTReconstructionMetadata.from_yaml(self._get_metadata_path())
