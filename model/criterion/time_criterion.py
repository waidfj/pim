from __future__ import annotations

import datetime
from ..exceptions import CriterionSyntaxError
from ..pir import PIR, format_datetime
from .base import Criterion
from .field_index import _TIME_FIELDS

class TimeCompareCriterion(Criterion):
    """Matches PIRs whose ``field_name`` (a time field) compares to
    ``time_value`` using operator ``<``, ``>`` or ``=``."""

    LT = "<"
    GT = ">"
    EQ = "="
    _OPS = {LT, GT, EQ}

    def __init__(
        self, field_name: str, op: str, time_value: datetime.datetime
    ) -> None:
        if field_name not in _TIME_FIELDS:
            raise CriterionSyntaxError(
                f"'{field_name}' is not a time field. "
                f"Known time fields: {sorted(_TIME_FIELDS)}"
            )
        if op not in self._OPS:
            raise CriterionSyntaxError(
                f"Unknown time operator '{op}'. Use one of {sorted(self._OPS)}"
            )
        if not isinstance(time_value, datetime.datetime):
            raise CriterionSyntaxError("time value must be a datetime")
        self._field_name = field_name
        self._op = op
        self._time_value = time_value

    def matches(self, pir: PIR) -> bool:
        try:
            value = pir.get_field(self._field_name)
        except Exception:
            return False
        if not isinstance(value, datetime.datetime):
            return False
        if self._op == self.LT:
            return value < self._time_value
        if self._op == self.GT:
            return value > self._time_value
        return value == self._time_value

    def __str__(self) -> str:
        return (
            f"{self._field_name}{self._op}"
            f"{format_datetime(self._time_value)}"
        )
