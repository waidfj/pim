from __future__ import annotations

from .pim_model_error import PIMModelError


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
