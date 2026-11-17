from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
from ..exceptions import InvalidFieldValueError, UnknownFieldError
from .base import PIR, _register_pir_class
from .datetime_utils import _coerce_time, format_datetime, parse_datetime

@_register_pir_class
class Event(PIR):
    """A scheduled event with an optional alarm.  Backs user story US4."""

    TYPE_NAME = "event"
    _FIELDS = ("description", "starting_time", "alarm")
    _FIELD_KINDS = {
        "description": "text",
        "starting_time": "time",
        "alarm": "time",
    }

    def __init__(
        self,
        description: str = "",
        starting_time: Any = None,
        alarm: Any = None,
        pir_id: Optional[int] = None,
    ) -> None:
        super().__init__(pir_id)
        if not isinstance(description, str):
            raise InvalidFieldValueError("description", description, "string")
        self._description = description
        self._starting_time = self._coerce_time(starting_time)
        self._alarm = self._coerce_time(alarm)

    @staticmethod
    def _coerce_time(value: Any) -> Optional[datetime.datetime]:
        return _coerce_time(value, "(time field)")

    def get_field(self, name: str) -> Any:
        if name == "description":
            return self._description
        if name == "starting_time":
            return self._starting_time
        if name == "alarm":
            return self._alarm
        raise UnknownFieldError(name)

    def set_field(self, name: str, value: Any) -> None:
        if name == "description":
            if not isinstance(value, str):
                raise InvalidFieldValueError(name, value, "string")
            self._description = value
            return
        if name == "starting_time":
            self._starting_time = self._coerce_time(value)
            return
        if name == "alarm":
            self._alarm = self._coerce_time(value)
            return
        raise UnknownFieldError(name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "type": self.TYPE_NAME,
            "description": self._description,
            "starting_time": (
                format_datetime(self._starting_time)
                if self._starting_time
                else None
            ),
            "alarm": (
                format_datetime(self._alarm) if self._alarm else None
            ),
        }

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            description=data.get("description", ""),
            starting_time=data.get("starting_time"),
            alarm=data.get("alarm"),
            pir_id=data.get("id"),
        )

    def __str__(self) -> str:
        return (
            f"[Event #{self._id}] description={self._description!r}, "
            f"starting_time={format_datetime(self._starting_time) if self._starting_time else 'None'}, "
            f"alarm={format_datetime(self._alarm) if self._alarm else 'None'}"
        )
