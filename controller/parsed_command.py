"""Structured representation of a tokenized PIM command."""

from __future__ import annotations

from typing import Dict, List


class ParsedCommand:
    """The structured form of a single input line."""

    __slots__ = ("verb", "positionals", "kwargs", "raw")

    def __init__(
        self,
        verb: str,
        positionals: List[str],
        kwargs: Dict[str, str],
        raw: str,
    ) -> None:
        self.verb = verb
        self.positionals = positionals
        self.kwargs = kwargs
        self.raw = raw

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"ParsedCommand(verb={self.verb!r}, "
            f"positionals={self.positionals!r}, kwargs={self.kwargs!r})"
        )
