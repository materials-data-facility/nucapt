"""Operations relating to managing data folders on NUCAPT servers"""

import os
import re
from abc import abstractmethod, ABCMeta
from datetime import date
from glob import glob

import six
import yaml

import nucapt
from nucapt.exceptions import DatasetParseException
from nucapt.metadata import APTDataCollectionMetadata, GeneralMetadata, APTSampleGeneralMetadata, \
    APTReconstructionMetadata, APTSamplePreparationMetadata, APTAnalysisMetadata

# Key variables
module_dir = os.path.dirname(os.path.abspath(nucapt.__file__))
template_path = os.path.join(module_dir, '..', 'template_directory')
data_path = nucapt.app.config['WORKING_PATH']


@six.add_metaclass(ABCMeta)
class DataDirectory:
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

    def _find_file(self, file_type, allow_none=False):
        """File a file with a certain extension in this directory

        :param file_type: str, extension of target file
        :param allow_none: bool, whether to return None if no file found
            rather than raising an exception
        :return: Path to target file"""
        r = re.compile(r'\.%s' % file_type, re.IGNORECASE)
        file = [f for f in os.listdir(self.path) if r.search(f)]
        if len(file) == 0:
            if allow_none:
                return None
            else:
                raise DatasetParseException('No %s files. Somehow, it got deleted.' % file_type)
        if len(file) > 1:
            raise DatasetParseException('More than 1 %s file! Should be exactly one' % file_type)
        return os.path.join(self.path, file[0])


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
        metadata['dates'] = {'creation_date': date.today().strftime("%d%b%y")}

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
        for sub_path in glob(os.path.join(path, "*", "GeneralMetadata.yaml")):
            sub_path = os.path.dirname(sub_path)

            # Get "name" of directory
            try:
                output[sub_path] = cls.load_dataset_by_path(sub_path)
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

    def mark_as_published(self, publication_id, landing_url):
        """Mark this dataset as in the process of submission

        :param publication_id: string, identification information"""

        data = {'publication_id': publication_id,
                'landing_url': landing_url,
                'submission_date': date.today().strftime("%d%b%y")}
        yaml.dump(data, open(os.path.join(self.path, 'PublicationData.yaml'), 'w'))

    def is_published(self):
        """:return: bool, whether this dataset has been published"""
        return os.path.isfile(os.path.join(self.path, 'PublicationData.yaml'))


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
        preparation = APTSamplePreparationMetadata.from_form(form.preparation_form)

        # Create a directory and save metadata in it
        sample_name = form.sample_name.data
        path = os.path.join(data_path, dataset_name, sample_name)

        # Add the creation date
        general['creation_date'] = date.today().strftime("%d%b%y")

        #   Check if that path exists
        if os.path.isdir(path):
            raise DatasetParseException('Sample %s already exists for dataset %s'%(sample_name, dataset_name))
        os.mkdir(path)

        # Instantiate the object
        sample = cls(dataset_name, sample_name, path)

        general.to_yaml(sample._get_sample_information_path())
        collection.to_yaml(sample._get_collection_metadata_path())
        preparation.to_yaml(sample._get_preparation_metadata_path())

        return sample_name

    def _update_metadata_from_form(self, cls, path, form):
        """Take metadata from form, save to disk

        :param cls: Metadata handling class
        :param path: Path to save metadata
        :param form: Form to parse
        :return: Path to metadata
        """

        metadata = cls.from_form(form)
        metadata.to_yaml(path)
        return path

    def _get_sample_information_path(self):
        """Get path to APT sample information

        :return: str, path
        """
        return os.path.join(self.path, 'SampleInformation.yaml')

    def update_sample_information(self, form):
        """Save sample information to disk

        :param form: APTSampleDescriptionForm, metadata object
        :return: path to metadata"""

        return self._update_metadata_from_form(APTSampleGeneralMetadata,
                                               self._get_sample_information_path(),
                                               form)

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

        :param form: Metadata to be parsed
        :return: path to metadata"""

        return self._update_metadata_from_form(APTDataCollectionMetadata,
                                               self._get_collection_metadata_path(),
                                               form)

    def load_collection_metadata(self):
        """Load in APT collection method metadata, if available

        :return: APTDataCollectionMetadata if present, else None"""

        if os.path.isfile(self._get_collection_metadata_path()):
            return APTDataCollectionMetadata.from_yaml(self._get_collection_metadata_path())
        return None

    def _get_preparation_metadata_path(self):
        """Get path to sample preparation metadata

        :return: str, path
        """
        return os.path.join(self.path, 'SamplePreparation.yaml')

    def update_preparation_metadata(self, form):
        """Update preparation metadata

        :param form: Form holding new metadata
        :return: path to metadata
        """

        self._update_metadata_from_form(APTSamplePreparationMetadata,
                                        self._get_preparation_metadata_path(),
                                        form)

    def load_preparation_metadata(self):
        """Load metadata about how this sample was prepared

        :return: APTSamplePreperationMetadata"""

        return APTSamplePreparationMetadata.from_yaml(self._get_preparation_metadata_path())

    def get_preparation_metadata(self):
        """Load the sample preparation information from disk

        :return: dict, Preparation metadata
        """
        return APTSamplePreparationMetadata.from_yaml(
            self._get_preparation_metadata_path()
        )

    def get_rhit_path(self):
        """Get the path to the RHIT file

        :return: str, RHIT path. `None` if file not found"""

        # Find the *RHIT file in this directory
        return self._find_file("RHIT", allow_none=True)

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
                    errors.extend(["%s:%s" % (recon_name, x) for x in exc.errors])
            except DatasetParseException as exc:
                errors.extend(["%s:%s" % (recon_name, x) for x in exc.errors])
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
    def _make_name(*args):
        return '_'.join(args)

    @classmethod
    def create_reconstruction(cls, form, dataset_name, sample_name, tip_image):
        """Add a new construction to a sample

        :param form: AddReconstructionForm, Form from web service
        :param dataset_name: str, name of dataset
        :param sample_name: str, name of sample
        :param tip_image: str, path to tip image
        :return: str, Reconstruction name
        """

        # Get the recon_name
        recon_name = form.data['name']

        # Validate metadata
        form_data = dict(form.data)
        del form_data['name']
        del form_data['pos_file']
        del form_data['rrng_file']

        #   Remove fields with None values
        for f in ['tip_radius', 'tip_image', 'shank_angle']:
            if form_data[f] is None or form_data[f] is '':
                del form_data[f]
        metadata = APTReconstructionMetadata(**form_data)
        metadata['creation_date'] = date.today().strftime("%d%b%y")

        # Add path to tip image
        if tip_image is not None:
            metadata['tip_image'] = tip_image

        # Make the directory and save the metadata
        path = cls._make_path(dataset_name, sample_name, recon_name)
        if os.path.isdir(path):
            raise DatasetParseException('Recon %s already exists' % (recon_name))
        os.mkdir(path)
        recon = cls.load_dataset_by_path(path)

        # Save the metadata
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

    def get_pos_file(self):
        """Get the POS file for this directory

        :return: str, path to POS file"""

        return self._find_file("POS")

    def get_rrng_file(self):
        """Get the RRNG file for this directory

        :return: str, path to RRNG file"""

        return self._find_file('RRNG')

    def get_analyses(self):
        """Gather the names and metadata of folders containing analyses"""

        # Load the results
        analyses = dict()
        for file in glob("%s/*/AnalysisMetadata.yaml" % self.path):
            dirname = os.path.basename(os.path.dirname(file))
            try:
                analyses[dirname] = yaml.load(open(file))
            except Exception as e:
                analyses[dirname] = {'title': '<b>Metadata file corrupted!</b>'}
        return analyses


class APTAnalysisDirectory(DataDirectory):
    """Directory associated with the analysis performed on reconstructed APT data"""

    def __init__(self, dataset_name, sample_name, recon_name, analysis_dir, path):
        """Do not use, use load by name instead"""
        super(APTAnalysisDirectory, self).__init__("_".join([dataset_name, sample_name, recon_name, analysis_dir]),
                                                   path)
        self.dataset_name = dataset_name
        self.sample_name = sample_name
        self.recon_name = recon_name
        self.analysis_dir = analysis_dir

    @classmethod
    def load_dataset_by_path(cls, path):
        temp_path, recon_name = os.path.split(path)
        temp_path, sample_name = os.path.split(temp_path)
        temp_path, dataset_name = os.path.split(temp_path)
        temp_path, analysis_dir = os.path.split(temp_path)
        return cls(dataset_name, sample_name, recon_name, analysis_dir, path)

    @classmethod
    def load_dataset_by_name(cls, dataset_name, sample_name, recon_name, analysis_dir):
        """Load an APT reconstruction by name

        :param dataset_name: str, name of dataset
        :param sample_name: str, name of sample
        :param recon_name: str, name of reconstruction
        :param analysis_dir: str, path of the analysis directory
        :return: APTReconstruction
        """

        path = cls._make_path(dataset_name, sample_name, recon_name, analysis_dir)
        return cls(dataset_name, sample_name, recon_name, analysis_dir, path)

    @classmethod
    def _make_path(cls, dataset_name, sample_name, recon_name, analysis_dir):
        return os.path.join(data_path, dataset_name, sample_name, recon_name, analysis_dir)

    def _get_metadata_path(self):
        """Get the path to the metadata file"""
        return os.path.join(self.path, 'AnalysisMetadata.yaml')

    @classmethod
    def create_analysis_directory(cls, form, dataset_name, sample_name, recon_name):
        """Add a new construction to a sample

        :param form: AnalysisForm, Form from web service
        :param dataset_name: str, name of dataset
        :param sample_name: str, name of sample
        :param recon_name: str, name of reconstruction
        :return: str, Reconstruction name
        """

        # Get the form data
        form_data = dict(form.data)

        # Get the analysis name
        analysis_name = form_data['folder_name']

        # Create the metadata
        metadata = APTAnalysisMetadata.from_form(form)
        metadata['creation_date'] = date.today().strftime("%d%b%y")

        # Make the directory and save the metadata
        path = cls._make_path(dataset_name, sample_name, recon_name, analysis_name)
        if os.path.isdir(path):
            raise DatasetParseException('Analysis named %s already exists' % analysis_name)
        os.mkdir(path)
        recon = cls.load_dataset_by_path(path)
        metadata.to_yaml(recon._get_metadata_path())

        return analysis_name

    def update_metadata(self, form):
        """Update the metadata for this analysis directory

        :param form: AnalysisForm, form containing new metadata"""

        # Read in the new metadata
        new_metadata = APTAnalysisMetadata.from_form(form)

        # Old metadata has the creation date
        old_metadata = APTAnalysisMetadata.from_yaml(self._get_metadata_path())
        old_metadata.metadata.update(new_metadata.metadata)
        old_metadata.to_yaml(self._get_metadata_path())

    def load_metadata(self):
        """Read the metadata for this entry"""

        return APTAnalysisMetadata.from_yaml(self._get_metadata_path())