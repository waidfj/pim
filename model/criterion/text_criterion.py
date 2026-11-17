from __future__ import annotations

from ..exceptions import CriterionSyntaxError
from ..pir import PIR
from .base import Criterion
from .field_index import _TEXT_FIELDS

class TextContainsCriterion(Criterion):
    """Matches PIRs whose ``field_name`` is a string that contains
    ``substring`` (case-sensitive, substring anywhere in the value)."""

    def __init__(self, field_name: str, substring: str) -> None:
        if field_name not in _TEXT_FIELDS:
            raise CriterionSyntaxError(
                f"'{field_name}' is not a text field. "
                f"Known text fields: {sorted(_TEXT_FIELDS)}"
            )
        if not isinstance(substring, str):
            raise CriterionSyntaxError("text substring must be a string")
        self._field_name = field_name
        self._substring = substring

    def matches(self, pir: PIR) -> bool:
        try:
            value = pir.get_field(self._field_name)
        except Exception:
            return False
        if not isinstance(value, str):
            return False
        return self._substring in value

    def __str__(self) -> str:
        return f"{self._field_name}~{self._substring!r}"
