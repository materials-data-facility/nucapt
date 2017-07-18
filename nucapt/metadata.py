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
        errors = [e.message for e in validator.iter_errors(self.metadata)]
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
                yaml.dump(self.metadata, fp)
        except IOError as exc:
            raise DatasetParseException('Save for YAML file failed: ' + str(exc))


class APTDataCollectionMetadata(MetadataHolder):
    """Class to store the APT metadata"""

    def _get_schema_path(self):
        return os.path.join(schema_path, "CollectionMetadata.json")


class GeneralMetadata(MetadataHolder):
    """Class to hold general metadata about dataste"""

    def _get_schema_path(self):
        return os.path.join(schema_path, "GeneralMetadata.json")