from __future__ import annotations

import datetime
from ..exceptions import InvalidFieldValueError

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
