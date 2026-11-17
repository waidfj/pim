from __future__ import annotations

from .pim_model_error import PIMModelError


class UnknownFieldError(PIMModelError):
    """Raised when an operation references a field that does not exist on a
    PIR (for example, asking a Contact for its ``deadline``)."""

    def __init__(self, field_name: str):
        super().__init__(f"Unknown field: '{field_name}'")
        self.field_name = field_name
