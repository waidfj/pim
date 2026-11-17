from __future__ import annotations

from .base import Criterion
from .composite import AndCriterion, NotCriterion, OrCriterion
from .field_index import (
    _refresh_field_index,
    known_fields,
    known_text_fields,
    known_time_fields,
)
from .text_criterion import TextContainsCriterion
from .time_criterion import TimeCompareCriterion
from .type_criterion import TypeCriterion

__all__ = [
    "Criterion",
    "TypeCriterion",
    "TextContainsCriterion",
    "TimeCompareCriterion",
    "AndCriterion",
    "OrCriterion",
    "NotCriterion",
    "known_fields",
    "known_text_fields",
    "known_time_fields",
]