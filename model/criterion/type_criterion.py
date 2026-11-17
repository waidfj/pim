from __future__ import annotations

from ..exceptions import CriterionSyntaxError
from ..pir import PIR, known_type_names
from .base import Criterion

class TypeCriterion(Criterion):
    """Matches PIRs whose canonical type name equals ``type_name``."""

    def __init__(self, type_name: str) -> None:
        if type_name not in known_type_names():
            raise CriterionSyntaxError(
                f"Unknown PIR type '{type_name}'. "
                f"Known types: {sorted(known_type_names())}"
            )
        self._type_name = type_name

    def matches(self, pir: PIR) -> bool:
        return pir.get_type() == self._type_name

    def __str__(self) -> str:
        return f"type={self._type_name}"
