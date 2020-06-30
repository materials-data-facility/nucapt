import json
import os

import yaml

from nucapt.exceptions import DatasetParseException

module_dir = os.path.dirname(os.path.abspath(__file__))


class MetadataHolder:
    """General class for files that hold metadata"""

    def __init__(self, **kwargs):
        """Please use `load_from_file` instead"""
        self.metadata = kwargs

    def __getitem__(self, item):
        return self.metadata[item]

    def __setitem__(self, key, value):
        self.metadata[key] = value

    @classmethod
    def from_form(cls, form):
        """Generate this metadata class from a form object

        :param form: Form, webpage form"""

        metadata = form.data
        return cls(**metadata)

    @classmethod
    def from_yaml(cls, path):
        """Load metadata from YAML file

         :param path: str, path to YAML file"""

        if not os.path.isfile(path):
            raise DatasetParseException('Metadata file not found: ' + path)

        with open(path, 'r') as fp:
            try:
                data = yaml.load(fp)
            except:
                raise DatasetParseException('Metadata file not valid YAML: ' + path)
            return cls(**data)

    def to_yaml(self, path):
        """Save metadata to a YML file"""

        try:
            with open(path, 'w') as fp:
                yaml.safe_dump(self.metadata, fp, allow_unicode=True)
        except IOError as exc:
            raise DatasetParseException('Save for YAML file failed: ' + str(exc))


class APTDataCollectionMetadata(MetadataHolder):
    """Class to store the APT metadata"""
    pass


class GeneralMetadata(MetadataHolder):
    """Class to hold general metadata about a dataset"""
    pass


class APTSampleGeneralMetadata(MetadataHolder):
    """Class to hold general metadata about a single APT sample"""
    pass


class APTReconstructionMetadata(MetadataHolder):
    """Class to hold metadata about a reconstruction"""
    pass


class APTSamplePreparationMetadata(MetadataHolder):
    """Class to hold metadata about sample preparation"""

    @classmethod
    def from_form(cls, form):
        metadata = form.data

        # Get the method
        method = metadata['preparation_method']

        # Keep only the metadata from that method
        if method == 'electropolish':
            del metadata['fib_lift_out']
        else:
            del metadata['electropolish']

        return cls(**metadata)


class APTAnalysisMetadata(MetadataHolder):
    @classmethod
    def from_form(cls, form):
        metadata = form.data

        # Remove the fields 'file' and 'folder_name'
        for k in ['file', 'folder_name']:
            if k in metadata:
                del metadata[k]

        # Generate the form
        return cls(**metadata)
