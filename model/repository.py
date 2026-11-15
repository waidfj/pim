"""In-memory collection of PIRs with search support.

The :class:`PIRRepository` is the only aggregate root in the model layer:
all PIRs live inside a repository, and the storage layer serialises /
deserialises one repository at a time.  Operations are deliberately
synchronous and in-memory; persistence is a separate concern handled by
:class:`model.storage.PIMStorage`.

The repository exposes CRUD operations, an iteration protocol and a
:meth:`search` method that takes a :class:`model.criterion.Criterion` and
returns the matching PIRs in id order.  This is the single integration point
between the repository and the criterion subsystem; everything else just
moves PIR objects around.
"""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Optional

from .criterion import Criterion
from .exceptions import (
    DuplicatePIRIdError,
    PIRNotFoundError,
)
from .pir import PIR


class PIRRepository:
    """A simple in-memory store for :class:`PIR` instances keyed by id.

    The repository owns no persistence of its own; callers use
    :func:`model.storage.PIMStorage.save` / :func:`model.storage.PIMStorage.load`
    when they want to round-trip the contents through a ``.pim`` file.
    """

    def __init__(self) -> None:
        self._pirs: Dict[int, PIR] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def add(self, pir: PIR) -> None:
        """Insert ``pir`` into the repository.

        Raises :class:`DuplicatePIRIdError` if a PIR with the same id is
        already present (which would indicate either a bug in the caller or
        a load collision that should be surfaced loudly rather than
        silently).
        """
        if not isinstance(pir, PIR):
            raise TypeError(f"expected PIR, got {type(pir).__name__}")
        if pir.id in self._pirs:
            raise DuplicatePIRIdError(pir.id)
        self._pirs[pir.id] = pir

    def get(self, pir_id: int) -> PIR:
        """Return the PIR with ``pir_id``.

        Raises :class:`PIRNotFoundError` if no such PIR exists.
        """
        if pir_id not in self._pirs:
            raise PIRNotFoundError(pir_id)
        return self._pirs[pir_id]

    def remove(self, pir_id: int) -> PIR:
        """Remove and return the PIR with ``pir_id``.

        Raises :class:`PIRNotFoundError` if no such PIR exists.
        """
        if pir_id not in self._pirs:
            raise PIRNotFoundError(pir_id)
        return self._pirs.pop(pir_id)

    def update(self, pir_id: int, field: str, value: object) -> PIR:
        """Update ``field`` on the PIR with ``pir_id`` to ``value``.

        Returns the updated PIR so the CLI can immediately render the new
        state to the user.  Delegates field validation to the PIR's
        :meth:`PIR.set_field`, which raises :class:`UnknownFieldError` or
        :class:`InvalidFieldValueError` as appropriate.
        """
        pir = self.get(pir_id)
        pir.set_field(field, value)
        return pir

    # ------------------------------------------------------------------
    # Bulk access
    # ------------------------------------------------------------------
    def all(self) -> List[PIR]:
        """Return every PIR in the repository, sorted by id ascending so
        output is deterministic across runs."""
        return [self._pirs[k] for k in sorted(self._pirs)]

    def search(self, criterion: Criterion) -> List[PIR]:
        """Return every PIR in the repository that matches ``criterion``,
        sorted by id ascending."""
        if not isinstance(criterion, Criterion):
            raise TypeError(
                f"expected Criterion, got {type(criterion).__name__}"
            )
        return [
            self._pirs[k]
            for k in sorted(self._pirs)
            if criterion.matches(self._pirs[k])
        ]

    def clear(self) -> None:
        """Remove every PIR from the repository.  Mainly useful before a
        fresh :func:`PIMStorage.load` when the caller wants to discard the
        current in-memory state."""
        self._pirs.clear()

    # ------------------------------------------------------------------
    # Dunder protocols
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._pirs)

    def __contains__(self, pir_id: object) -> bool:
        return pir_id in self._pirs

    def __iter__(self) -> Iterator[PIR]:
        for k in sorted(self._pirs):
            yield self._pirs[k]

    def __repr__(self) -> str:
        return f"<PIRRepository count={len(self._pirs)}>"

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_iterable(cls, pirs: Iterable[PIR]) -> "PIRRepository":
        """Build a repository from an iterable of PIRs.  Useful in tests
        and when merging multiple ``.pim`` files."""
        repo = cls()
        for pir in pirs:
            repo.add(pir)
        return repo
