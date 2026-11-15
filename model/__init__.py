"""The ``model`` package -- PIM system model layer.

This package contains everything the system knows about *what* a PIR is and
*how* PIRs are stored and searched.  It deliberately has no knowledge of the
CLI, the terminal, or anything user-facing; that lives in the
``controller`` and ``view`` packages.

Public API re-exported here for convenience:

* :class:`PIR`, :class:`PlainText`, :class:`Task`, :class:`Event`,
  :class:`Contact` -- PIR types
* :class:`PIRRepository` -- in-memory store
* :class:`PIMStorage` -- ``.pim`` file I/O
* :class:`Criterion` (and friends) -- search DSL
* :class:`PIMModelError` and all specific exception subclasses

Code outside the model should only ever import from this top-level package,
never from the individual submodules; that way the module layout remains free
to evolve.
"""

from .criterion import (
    AndCriterion,
    Criterion,
    NotCriterion,
    OrCriterion,
    TextContainsCriterion,
    TimeCompareCriterion,
    TypeCriterion,
)
from .criterion import (
    known_fields,
    known_text_fields,
    known_time_fields,
)
from .exceptions import (
    CriterionSyntaxError,
    DuplicatePIRIdError,
    InvalidFileExtensionError,
    InvalidFieldValueError,
    PIMModelError,
    PIRNotFoundError,
    StorageCorruptionError,
    UnknownFieldError,
    UnknownPIRTypeError,
)
from .pir import (
    Contact,
    Event,
    PlainText,
    PIR,
    Task,
    all_pir_types,
    format_datetime,
    known_type_names,
    parse_datetime,
)
from .repository import PIRRepository
from .storage import PIMStorage

__all__ = [
    # PIR types
    "PIR",
    "PlainText",
    "Task",
    "Event",
    "Contact",
    "all_pir_types",
    "known_type_names",
    "parse_datetime",
    "format_datetime",
    # Repository
    "PIRRepository",
    # Storage
    "PIMStorage",
    # Criterion
    "Criterion",
    "TypeCriterion",
    "TextContainsCriterion",
    "TimeCompareCriterion",
    "AndCriterion",
    "OrCriterion",
    "NotCriterion",
    "known_fields",
    "known_text_fields",
    "known_time_fields",
    # Exceptions
    "PIMModelError",
    "UnknownFieldError",
    "InvalidFieldValueError",
    "PIRNotFoundError",
    "DuplicatePIRIdError",
    "InvalidFileExtensionError",
    "StorageCorruptionError",
    "UnknownPIRTypeError",
    "CriterionSyntaxError",
]
