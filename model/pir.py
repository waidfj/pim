"""Personal Information Record (PIR) classes.

This module defines the four PIR types supported by the system and a common
abstract base class :class:`PIR`.  All PIRs share:

* an integer ``id`` that uniquely identifies the record inside a single
  in-memory :class:`model.repository.PIRRepository`;
* the ability to expose their fields through :meth:`get_field` /
  :meth:`set_field`, which lets the search-criterion layer treat every PIR
  polymorphically instead of doing ``isinstance`` checks;
* JSON-friendly :meth:`to_dict` / :meth:`from_dict` so the storage layer can
  round-trip them through a ``.pim`` file without knowing about individual
  subclasses.

The ``id`` counter is process-global; when records are loaded back from a
``.pim`` file the counter is bumped past the highest loaded id so the next
freshly-created record does not collide with a restored one.
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .exceptions import (
    InvalidFieldValueError,
    UnknownFieldError,
    UnknownPIRTypeError,
)


# ---------------------------------------------------------------------------
# Datetime helpers
# ---------------------------------------------------------------------------
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def parse_datetime(value: str) -> datetime.datetime:
    """Parse a strict ISO-ish datetime string ``YYYY-MM-DDTHH:MM:SS``.

    The accepted format is intentionally narrow so that the criterion DSL
    and the CLI share one canonical representation.  A trailing ``Z`` or
    fractional seconds are *not* accepted to keep the parser simple and the
    output predictable.
    """
    if not isinstance(value, str):
        raise InvalidFieldValueError("(inline)", value, "ISO datetime string")
    try:
        return datetime.datetime.strptime(value, _DATETIME_FORMAT)
    except ValueError as exc:
        raise InvalidFieldValueError(
            "(inline)", value, f"ISO datetime ({_DATETIME_FORMAT})"
        ) from exc


def format_datetime(value: datetime.datetime) -> str:
    """Render a :class:`~datetime.datetime` back into the canonical string
    form used everywhere in the system."""
    return value.strftime(_DATETIME_FORMAT)


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------
class PIR(ABC):
    """Abstract base class for every kind of Personal Information Record.

    Concrete subclasses must implement :meth:`get_field`, :meth:`set_field`,
    :meth:`to_dict`, :meth:`field_names` and :meth:`__str__`.  They typically
    also override :meth:`_set_field_raw` for validation but the default
    implementation is fine for plain string fields.
    """

    # Process-global id counter for newly-created PIRs.  Bumped past the
    # highest id seen via :meth:`_bump_id_counter` so loaded records don't
    # collide with freshly-created ones.
    _next_id: int = 1

    # Subclasses override this with the canonical type name persisted into
    # ``.pim`` files.  Using a class attribute keeps :meth:`to_dict` /
    # :meth:`from_dict` symmetric and avoids reflection.
    TYPE_NAME: str = "pir"

    def __init__(self, pir_id: Optional[int] = None) -> None:
        if pir_id is None:
            pir_id = PIR._next_id
            PIR._next_id += 1
        else:
            # When restoring from a file, push the counter past the supplied
            # id so future creations don't collide.
            PIR._bump_id_counter(pir_id)
        self._id = int(pir_id)

    # -- id ---------------------------------------------------------------
    @property
    def id(self) -> int:
        return self._id

    @classmethod
    def _bump_id_counter(cls, loaded_id: int) -> None:
        """Move the global id counter past ``loaded_id`` if it isn't
        already."""
        if loaded_id >= PIR._next_id:
            PIR._next_id = loaded_id + 1

    @classmethod
    def reset_id_counter(cls, start: int = 1) -> None:
        """Reset the process-global id counter.  Intended for unit tests so
        that test runs are deterministic and independent of each other."""
        PIR._next_id = max(1, start)

    # -- type -------------------------------------------------------------
    @classmethod
    def get_type(cls) -> str:
        """Return the canonical type name of this PIR class."""
        return cls.TYPE_NAME

    # -- field protocol ---------------------------------------------------
    @classmethod
    @abstractmethod
    def field_names(cls) -> tuple:
        """Return the tuple of field names exposed by this PIR type.  Used by
        the criterion layer to validate field references at parse time and
        by the CLI to render editable field lists."""
        raise NotImplementedError

    @classmethod
    def field_kinds(cls) -> Dict[str, str]:
        """Return a mapping ``field_name -> kind`` where ``kind`` is one of
        ``"text"`` or ``"time"``.  Used by the criterion layer to know which
        operators are valid for each field without instantiating the PIR
        (which would yield ``None`` defaults that look like text).  The
        default implementation looks at the class-level ``_FIELD_KINDS``
        attribute; subclasses set that attribute at class scope.
        """
        return dict(getattr(cls, "_FIELD_KINDS", {}))

    @abstractmethod
    def get_field(self, name: str) -> Any:
        """Return the current value of field ``name``."""
        raise NotImplementedError

    @abstractmethod
    def set_field(self, name: str, value: Any) -> None:
        """Update field ``name`` to ``value``.  Implementations must raise
        :class:`UnknownFieldError` for unknown names and
        :class:`InvalidFieldValueError` for unparseable values."""
        raise NotImplementedError

    # -- serialisation ----------------------------------------------------
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialise this PIR into a JSON-friendly dict.  The dict must
        include the canonical ``type`` so :meth:`from_dict` can dispatch to
        the correct subclass."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PIR":
        """Reconstruct a PIR from the dict produced by :meth:`to_dict`.

        Dispatches to the subclass indicated by ``data['type']`` and raises
        :class:`UnknownPIRTypeError` if the type name is not registered.  The
        global id counter is bumped past the loaded id.
        """
        type_name = data.get("type")
        subclass = _PIR_REGISTRY.get(type_name)
        if subclass is None:
            raise UnknownPIRTypeError(type_name or "<missing>")
        return subclass._from_dict(data)

    @classmethod
    @abstractmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "PIR":
        """Subclass-specific rehydration hook called by :meth:`from_dict`
        after the type has been resolved."""
        raise NotImplementedError

    # -- matching ---------------------------------------------------------
    def matches(self, criterion) -> bool:
        """Convenience method that delegates to the criterion so callers can
        write ``pir.matches(crit)`` symmetrically with
        ``crit.matches(pir)``."""
        return criterion.matches(self)

    # -- display ----------------------------------------------------------
    @abstractmethod
    def __str__(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self._id}>"


# Registry of type_name -> subclass, populated at the bottom of this module
# so :meth:`PIR.from_dict` can dispatch.
_PIR_REGISTRY: Dict[str, type] = {}


def _register_pir_class(subclass: type) -> type:
    """Decorator that registers a PIR subclass in ``_PIR_REGISTRY`` under its
    ``TYPE_NAME``.  Used at class-definition time below."""
    _PIR_REGISTRY[subclass.TYPE_NAME] = subclass
    return subclass


# ---------------------------------------------------------------------------
# PlainText
# ---------------------------------------------------------------------------
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

    @classmethod
    def field_names(cls) -> tuple:
        return cls._FIELDS

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


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------
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
        if value is None or value == "":
            return None
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            return parse_datetime(value)
        raise InvalidFieldValueError("deadline", value, "ISO datetime")

    @classmethod
    def field_names(cls) -> tuple:
        return cls._FIELDS

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


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------
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
        if value is None or value == "":
            return None
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            return parse_datetime(value)
        raise InvalidFieldValueError("(time field)", value, "ISO datetime")

    @classmethod
    def field_names(cls) -> tuple:
        return cls._FIELDS

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


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------
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

    @classmethod
    def field_names(cls) -> tuple:
        return cls._FIELDS

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


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def all_pir_types() -> Dict[str, type]:
    """Return a copy of the type-name -> subclass registry."""
    return dict(_PIR_REGISTRY)


def known_type_names() -> tuple:
    """Return the canonical type names in a stable order (definition
    order)."""
    return tuple(_PIR_REGISTRY.keys())
