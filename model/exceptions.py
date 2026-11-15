"""Custom exception classes for the PIM model package.

All exceptions raised by the model layer inherit from PIMModelError so that
callers can catch any model-related error with a single except clause if they
wish, while still being able to catch specific subtypes when finer handling
is desired.
"""


class PIMModelError(Exception):
    """Base class for all errors raised by the PIM model package."""


class UnknownFieldError(PIMModelError):
    """Raised when an operation references a field that does not exist on a
    PIR (for example, asking a Contact for its ``deadline``)."""

    def __init__(self, field_name: str):
        super().__init__(f"Unknown field: '{field_name}'")
        self.field_name = field_name


class InvalidFieldValueError(PIMModelError):
    """Raised when a value supplied for a field cannot be interpreted as the
    type that field requires (for example, a non-ISO string for a time
    field)."""

    def __init__(self, field_name: str, value, expected_type: str):
        super().__init__(
            f"Invalid value for field '{field_name}': "
            f"expected {expected_type}, got {value!r}"
        )
        self.field_name = field_name
        self.value = value
        self.expected_type = expected_type


class PIRNotFoundError(PIMModelError):
    """Raised when a PIR with a given id cannot be located in the
    repository."""

    def __init__(self, pir_id: int):
        super().__init__(f"No PIR with id {pir_id}")
        self.pir_id = pir_id


class DuplicatePIRIdError(PIMModelError):
    """Raised when an attempt is made to insert a PIR whose id is already
    present in the repository."""

    def __init__(self, pir_id: int):
        super().__init__(f"A PIR with id {pir_id} already exists")
        self.pir_id = pir_id


class InvalidFileExtensionError(PIMModelError):
    """Raised when a file path used for save/load does not end in ``.pim``."""

    def __init__(self, path: str):
        super().__init__(
            f"File path must end with '.pim', got: {path!r}"
        )
        self.path = path


class StorageCorruptionError(PIMModelError):
    """Raised when a ``.pim`` file cannot be parsed or its contents cannot be
    rehydrated into PIR objects."""

    def __init__(self, path: str, detail: str):
        super().__init__(f"Corrupt .pim file {path!r}: {detail}")
        self.path = path
        self.detail = detail


class UnknownPIRTypeError(PIMModelError):
    """Raised when a serialized PIR dict refers to a type name that the model
    does not know about (forward-compatibility protection)."""

    def __init__(self, type_name: str):
        super().__init__(f"Unknown PIR type: '{type_name}'")
        self.type_name = type_name


class CriterionSyntaxError(PIMModelError):
    """Raised when a search-criterion expression cannot be tokenised or
    parsed."""

    def __init__(self, detail: str, position: int = -1):
        super().__init__(f"Criterion syntax error: {detail}")
        self.detail = detail
        self.position = position
