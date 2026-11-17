from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..exceptions import UnknownPIRTypeError

class PIR(ABC):
    """Abstract base class for every kind of Personal Information Record.

    Concrete subclasses must implement :meth:`get_field`, :meth:`set_field`,
    :meth:`to_dict`, :meth:`field_names` and :meth:`__str__`.  They typically
    also override :meth:`_set_field_raw` for validation but the default
    implementation is fine for plain string fields.
    """

    # Process-global id counter for newly-created PIRs.
    _next_id: int = 1

    # Subclasses override this with the canonical type name persisted into ``.pim`` files.
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
        """Move the global id counter past ``loaded_id`` if it isn't already."""
        if loaded_id >= PIR._next_id:
            PIR._next_id = loaded_id + 1

    @classmethod
    def reset_id_counter(cls, start: int = 1) -> None:
        """Reset the process-global id counter."""
        PIR._next_id = max(1, start)

    # -- type -------------------------------------------------------------
    @classmethod
    def get_type(cls) -> str:
        """Return the canonical type name of this PIR class."""
        return cls.TYPE_NAME

    # -- field protocol ---------------------------------------------------
    @classmethod
    def field_names(cls) -> tuple:
        """Return the tuple of field names exposed by this PIR type."""
        return cls._FIELDS

    @classmethod
    def field_kinds(cls) -> Dict[str, str]:
        """Return a mapping ``field_name -> kind`` where ``kind`` is one of
        ``"text"`` or ``"time"``."""
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

_PIR_REGISTRY: Dict[str, type] = {}

def _register_pir_class(subclass: type) -> type:
    """Decorator that registers a PIR subclass in ``_PIR_REGISTRY`` under its
    ``TYPE_NAME``.  Used at class-definition time below."""
    _PIR_REGISTRY[subclass.TYPE_NAME] = subclass
    return subclass
