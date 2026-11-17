from __future__ import annotations

from .pim_model_error import PIMModelError


class UnknownPIRTypeError(PIMModelError):
    """Raised when a serialized PIR dict refers to a type name that the model
    does not know about (forward-compatibility protection)."""

    def __init__(self, type_name: str):
        super().__init__(f"Unknown PIR type: '{type_name}'")
        self.type_name = type_name
