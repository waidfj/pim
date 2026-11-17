from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
from ..exceptions import InvalidFieldValueError, UnknownFieldError
from .base import PIR, _register_pir_class
from .datetime_utils import _coerce_time, format_datetime, parse_datetime

@_register_pir_class
class Task(PIR):
    """A to-do item with a description and a deadline.

    Backs user story US3.  The deadline is stored as a
    :class:`datetime.datetime`; passing a string at construction time is
    accepted for ergonomics and parsed with :func:`parse_datetime`.
    """

    TYPE_NAME = "task"
    _FIELDS = ("description", "deadline")
    _FIELD_KINDS = {"description": "text", "deadline": "time"}

    def __init__(
        self,
        description: str = "",
        deadline: Any = None,
        pir_id: Optional[int] = None,
    ) -> None:
        super().__init__(pir_id)
        if not isinstance(description, str):
            raise InvalidFieldValueError("description", description, "string")
        self._description = description
        self._deadline = self._coerce_deadline(deadline)

    @staticmethod
    def _coerce_deadline(value: Any) -> Optional[datetime.datetime]:
        return _coerce_time(value, "deadline")

    def get_field(self, name: str) -> Any:
        if name == "description":
            return self._description
        if name == "deadline":
            return self._deadline
        raise UnknownFieldError(name)

    def set_field(self, name: str, value: Any) -> None:
        if name == "description":
            if not isinstance(value, str):
                raise InvalidFieldValueError(name, value, "string")
            self._description = value
            return
        if name == "deadline":
            self._deadline = self._coerce_deadline(value)
            return
        raise UnknownFieldError(name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "type": self.TYPE_NAME,
            "description": self._description,
            "deadline": (
                format_datetime(self._deadline) if self._deadline else None
            ),
        }

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            description=data.get("description", ""),
            deadline=data.get("deadline"),
            pir_id=data.get("id"),
        )

    def __str__(self) -> str:
        return (
            f"[Task #{self._id}] description={self._description!r}, "
            f"deadline={format_datetime(self._deadline) if self._deadline else 'None'}"
        )
