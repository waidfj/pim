from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
from ..exceptions import InvalidFieldValueError, UnknownFieldError
from .base import PIR, _register_pir_class

@_register_pir_class
class PlainText(PIR):
    """A free-form note.  Backs user story US2."""

    TYPE_NAME = "plaintext"
    _FIELDS = ("text",)
    _FIELD_KINDS = {"text": "text"}

    def __init__(self, text: str = "", pir_id: Optional[int] = None) -> None:
        super().__init__(pir_id)
        if not isinstance(text, str):
            raise InvalidFieldValueError("text", text, "string")
        self._text = text

    def get_field(self, name: str) -> Any:
        if name == "text":
            return self._text
        raise UnknownFieldError(name)

    def set_field(self, name: str, value: Any) -> None:
        if name == "text":
            if not isinstance(value, str):
                raise InvalidFieldValueError(name, value, "string")
            self._text = value
            return
        raise UnknownFieldError(name)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self._id, "type": self.TYPE_NAME, "text": self._text}

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "PlainText":
        return cls(
            text=data.get("text", ""),
            pir_id=data.get("id"),
        )

    def __str__(self) -> str:
        return (
            f"[PlainText #{self._id}] text={self._text!r}"
        )
