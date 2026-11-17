"""Output sinks for the PIM CLI."""

from __future__ import annotations

import sys
from typing import IO, List, Optional


class Reporter:
    """Abstract output sink."""

    def write(self, text: str) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def write_line(self, text: str = "") -> None:
        self.write(text + "\n")


class PrintReporter(Reporter):
    """Concrete reporter that writes to an IO stream (defaults to ``sys.stdout``)."""

    def __init__(self, stream: Optional[IO[str]] = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def write(self, text: str) -> None:
        self._stream.write(text)
        self._stream.flush()


class InMemoryReporter(Reporter):
    """Reporter that buffers all output in memory for inspection.  Created
    specifically for the unit tests."""

    def __init__(self) -> None:
        self._buffer: List[str] = []

    def write(self, text: str) -> None:
        self._buffer.append(text)

    @property
    def text(self) -> str:
        return "".join(self._buffer)

    @property
    def lines(self) -> List[str]:
        return self.text.split("\n")
