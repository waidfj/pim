from __future__ import annotations

from ..pir import PIR
from .base import Criterion

class AndCriterion(Criterion):
    def __init__(self, left: Criterion, right: Criterion) -> None:
        self._left = left
        self._right = right

    def matches(self, pir: PIR) -> bool:
        return self._left.matches(pir) and self._right.matches(pir)

    def __str__(self) -> str:
        return f"({self._left} && {self._right})"

class OrCriterion(Criterion):
    def __init__(self, left: Criterion, right: Criterion) -> None:
        self._left = left
        self._right = right

    def matches(self, pir: PIR) -> bool:
        return self._left.matches(pir) or self._right.matches(pir)

    def __str__(self) -> str:
        return f"({self._left} || {self._right})"

class NotCriterion(Criterion):
    def __init__(self, inner: Criterion) -> None:
        self._inner = inner

    def matches(self, pir: PIR) -> bool:
        return not self._inner.matches(pir)

    def __str__(self) -> str:
        return f"!{self._inner}"
