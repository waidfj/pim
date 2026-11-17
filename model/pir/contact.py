from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
from ..exceptions import InvalidFieldValueError, UnknownFieldError
from .base import PIR, _register_pir_class

@_register_pir_class
class Contact(PIR):
    """A contact record with name, address and mobile number.  Backs user
    story US5."""

    TYPE_NAME = "contact"
    _FIELDS = ("name", "address", "mobile")
    _FIELD_KINDS = {
        "name": "text",
        "address": "text",
        "mobile": "text",
    }

    def __init__(
        self,
        name: str = "",
        address: str = "",
        mobile: str = "",
        pir_id: Optional[int] = None,
    ) -> None:
        super().__init__(pir_id)
        for fname, fval in (
            ("name", name),
            ("address", address),
            ("mobile", mobile),
        ):
            if not isinstance(fval, str):
                raise InvalidFieldValueError(fname, fval, "string")
        self._name = name
        self._address = address
        self._mobile = mobile

    def get_field(self, name: str) -> Any:
        if name == "name":
            return self._name
        if name == "address":
            return self._address
        if name == "mobile":
            return self._mobile
        raise UnknownFieldError(name)

    def set_field(self, name: str, value: Any) -> None:
        if name in ("name", "address", "mobile"):
            if not isinstance(value, str):
                raise InvalidFieldValueError(name, value, "string")
            setattr(self, f"_{name}", value)
            return
        raise UnknownFieldError(name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "type": self.TYPE_NAME,
            "name": self._name,
            "address": self._address,
            "mobile": self._mobile,
        }

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Contact":
        return cls(
            name=data.get("name", ""),
            address=data.get("address", ""),
            mobile=data.get("mobile", ""),
            pir_id=data.get("id"),
        )

    def __str__(self) -> str:
        return (
            f"[Contact #{self._id}] name={self._name!r}, "
            f"address={self._address!r}, mobile={self._mobile!r}"
        )
