"""Operations relating to managing data folders on NUCAPT servers"""

import os
import nucapt
from datetime import date
import shutil
import yaml
from six import string_types

# Key variables
module_dir = os.path.dirname(os.path.abspath(nucapt.__file__))
template_path = os.path.join(module_dir, '..', 'template_directory')
data_path = os.path.join(module_dir, '..', 'working_directory')


class DatasetParseException(Exception):
    """Holds error(s) detected during dataset parsing"""

    def __init__(self, errors):
        """Errors found during metadata parsing

        :param errors: str or list, errors found during parsing
        """
        if isinstance(errors, string_types):
            self.errors = [errors]
        else:
            self.errors = errors

    def __str__(self):
        return "<%d metadata errors>"%len(self.errors)


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
        if not os.path.isdir(metadata_dir):
            raise DatasetParseException('General metadata directory missing: %s'%metadata_dir)
        if not os.path.isfile(metadata_file):
            raise DatasetParseException('General metadata file not found: %s'%metadata_file)

        # Try to read in the metadata
        try:
            with open(metadata_file, 'r') as fp:
                metadata = yaml.load(fp)
        except ValueError as err:
            raise DatasetParseException('Metadata file not valid YML: ' + str(err))

        # Check that required data is present
        errors = []
        for tag in ['Title', 'Authors', 'Abstract', 'Date']:
            if tag not in metadata:
                errors.append('Metadata file missing required field: ' + tag)

        #   Check dates
        if 'Dates' in metadata:
            if 'Creation' not in metadata['Date']:
                errors.append('Missing required date: Creation')
        #    Check authors
        if 'Authors' in metadata:
            if not isinstance(metadata['Authors'], list):
                raise Exception('Authors metadata is not a list')
            for aid, author in enumerate(metadata['Authors']):
                for field in ['first_name', 'last_name', 'affiliation']:
                    if field not in author:
                        raise Exception('Author %d missing field: %s'%(aid, field))

        if len(errors) > 0:
            raise DatasetParseException(errors)
        print(metadata)
        return cls(name, path, metadata['Abstract'], metadata['Authors'],
                   metadata['Date'], metadata['Title'])

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
            Abstract=abstract,
            Title=title,
            Authors=authors,
            Date={'Creation':date.today().strftime("%d%b%y")}
        )

        # Write to disk
        metadata_path = os.path.join(my_path, 'General', 'GeneralMetadata.yml')
        with open(metadata_path, 'w') as fp:
            yaml.dump(my_metadata, fp)

        return my_name, my_path
