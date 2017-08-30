import json
import os

import yaml
from jsonschema import Draft4Validator

from nucapt.exceptions import DatasetParseException

module_dir = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(module_dir, 'schemas')


class MetadataHolder:
    """General class for files that hold metadata"""

    def __init__(self, **kwargs):
        """Please use `load_from_file` instead"""
        self.metadata = kwargs
        is_valid, errors = self.validate_data()
        if not is_valid:
            raise DatasetParseException(errors)

    def __getitem__(self, item):
        return self.metadata[item]

    def __setitem__(self, key, value):
        self.metadata[key] = value

    def _get_schema_path(self):
        """Get path to schemas
        
        :return: str, path to schema"""
        raise NotImplementedError()

    def validate_data(self):
        """Validate the metadata

        :return:
            - bool, whether this schema is valid
            - list, list of errors"""

        with open(self._get_schema_path()) as fp:
            schema = json.load(fp)
        validator = Draft4Validator(schema)
        is_valid = validator.is_valid(self.metadata)
        errors = [str(e) for e in validator.iter_errors(self.metadata)]
        return is_valid, errors

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

    def _get_schema_path(self):
        return os.path.join(schema_path, "CollectionMetadata.json")


class GeneralMetadata(MetadataHolder):
    """Class to hold general metadata about a dataset"""

    def _get_schema_path(self):
        return os.path.join(schema_path, "GeneralMetadata.json")


class APTSampleGeneralMetadata(MetadataHolder):
    """Class to hold general metadata about a single APT sample"""

    def _get_schema_path(self):
        return os.path.join(schema_path, "SampleMetadata.json")


class APTReconstructionMetadata(MetadataHolder):
    """Class to hold metadata about a reconstruction"""

    def _get_schema_path(self):
        return os.path.join(schema_path, "ReconstructionMetadata.json")


class APTSamplePreperationMetadata(MetadataHolder):
    """Class to hold metadata about sample preparation"""

    def _get_schema_path(self):
        return os.path.join(schema_path, "SamplePreparation.json")

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
