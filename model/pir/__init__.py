from __future__ import annotations

from typing import Dict
from .base import PIR, _PIR_REGISTRY, _register_pir_class
from .datetime_utils import format_datetime, parse_datetime
from .plaintext import PlainText
from .task import Task
from .event import Event
from .contact import Contact

def all_pir_types() -> Dict[str, type]:
    """Return a copy of the type-name -> subclass registry."""
    return dict(_PIR_REGISTRY)

def known_type_names() -> tuple:
    """Return the canonical type names in a stable order (definition
    order)."""
    return tuple(_PIR_REGISTRY.keys())

__all__ = [
    "PIR",
    "PlainText",
    "Task",
    "Event",
    "Contact",
    "parse_datetime",
    "format_datetime",
    "all_pir_types",
    "known_type_names",
]
