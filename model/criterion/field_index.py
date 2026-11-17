from __future__ import annotations

from ..pir import all_pir_types

def _build_field_index():
    """Return ``(text_fields, time_fields)`` sets collected across all
    registered PIR subclasses.  ``type`` is a virtual field handled
    separately.  Field kind is taken from each subclass's
    :meth:`PIR.field_kinds` classmethod rather than from default values, so
    that time fields whose default is ``None`` are still classified as time
    fields rather than silently as text fields."""
    text_fields = set()
    time_fields = set()
    for subclass in all_pir_types().values():
        for fname, kind in subclass.field_kinds().items():
            if kind == "time":
                time_fields.add(fname)
            else:
                text_fields.add(fname)
    return text_fields, time_fields

_TEXT_FIELDS: set

_TIME_FIELDS: set

def _refresh_field_index() -> None:
    """(Re)build the global text/time field index.  Called once at import
    time; tests that dynamically register PIR subclasses can call it again."""
    global _TEXT_FIELDS, _TIME_FIELDS
    _TEXT_FIELDS, _TIME_FIELDS = _build_field_index()

def known_text_fields() -> set:
    return set(_TEXT_FIELDS)

def known_time_fields() -> set:
    return set(_TIME_FIELDS)

def known_fields() -> set:
    return _TEXT_FIELDS | _TIME_FIELDS | {"type"}

_refresh_field_index()