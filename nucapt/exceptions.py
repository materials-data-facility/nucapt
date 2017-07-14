from six import string_types


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


