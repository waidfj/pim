"""Unit tests for :mod:`model.repository`.

These tests exercise the in-memory :class:`PIRRepository`:

* Adding PIRs and rejecting duplicates.
* Getting PIRs by id, including the missing-id error.
* Removing PIRs and getting the deleted object back.
* Updating fields via :meth:`update` and ensuring unknown / invalid field
  errors propagate.
* Searching by criterion -- but only the dispatch path; the criterion
  matching logic itself is tested in :mod:`tests.test_criterion`.
* Iteration order and ``__contains__`` semantics.

Tests assume the criterion subsystem works (cross-test dependency is
acceptable at the model layer; cross-layer dependencies are not).
"""

from __future__ import annotations

import unittest

from model import (
    Contact,
    Criterion,
    PlainText,
    PIR,
    PIRRepository,
    Task,
)
from model.exceptions import (
    DuplicatePIRIdError,
    PIRNotFoundError,
)


class TestPIRRepositoryCRUD(unittest.TestCase):
    """Functionality: add, get, remove, update on the repository."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.repo = PIRRepository()
        self.p1 = PlainText(text="alpha")
        self.p2 = PlainText(text="beta")
        self.repo.add(self.p1)
        self.repo.add(self.p2)

    def test_add_and_get(self) -> None:
        self.assertEqual(self.repo.get(self.p1.id), self.p1)
        self.assertEqual(self.repo.get(self.p2.id), self.p2)

    def test_add_duplicate_id_raises(self) -> None:
        with self.assertRaises(DuplicatePIRIdError):
            self.repo.add(PlainText(text="dup", pir_id=self.p1.id))

    def test_add_non_pir_raises(self) -> None:
        with self.assertRaises(TypeError):
            self.repo.add("not a PIR")  # type: ignore[arg-type]

    def test_get_missing_id_raises(self) -> None:
        with self.assertRaises(PIRNotFoundError):
            self.repo.get(9999)

    def test_remove_returns_deleted(self) -> None:
        removed = self.repo.remove(self.p1.id)
        self.assertIs(removed, self.p1)
        self.assertNotIn(self.p1.id, self.repo)

    def test_remove_missing_id_raises(self) -> None:
        with self.assertRaises(PIRNotFoundError):
            self.repo.remove(9999)

    def test_update_changes_field(self) -> None:
        updated = self.repo.update(self.p1.id, "text", "alpha-2")
        self.assertEqual(updated.get_field("text"), "alpha-2")
        # The update reflects in the repository's view too
        self.assertEqual(self.repo.get(self.p1.id).get_field("text"), "alpha-2")

    def test_update_unknown_field_propagates(self) -> None:
        with self.assertRaises(Exception):
            self.repo.update(self.p1.id, "name", "x")

    def test_update_missing_id_raises(self) -> None:
        with self.assertRaises(PIRNotFoundError):
            self.repo.update(9999, "text", "x")


class TestPIRRepositoryBulk(unittest.TestCase):
    """Functionality: all(), search(), __len__, __contains__, __iter__."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.repo = PIRRepository()
        self.p1 = PlainText(text="alpha")
        self.p2 = Task(description="task", deadline="2025-12-31T23:59:59")
        self.p3 = Contact(name="Alice", address="x", mobile="y")
        self.repo.add(self.p1)
        self.repo.add(self.p2)
        self.repo.add(self.p3)

    def test_all_returns_sorted_by_id(self) -> None:
        all_pirs = self.repo.all()
        ids = [p.id for p in all_pirs]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(all_pirs), 3)

    def test_len(self) -> None:
        self.assertEqual(len(self.repo), 3)

    def test_contains(self) -> None:
        self.assertIn(self.p1.id, self.repo)
        self.assertNotIn(9999, self.repo)

    def test_iter_yields_pirs_in_id_order(self) -> None:
        ids = [p.id for p in self.repo]
        self.assertEqual(ids, [self.p1.id, self.p2.id, self.p3.id])

    def test_search_dispatches_criterion(self) -> None:
        # type=task matches exactly the Task p2
        crit = Criterion.parse("type=task")
        results = self.repo.search(crit)
        self.assertEqual(len(results), 1)
        self.assertIs(results[0], self.p2)

    def test_search_empty_when_no_match(self) -> None:
        crit = Criterion.parse("type=event")
        self.assertEqual(self.repo.search(crit), [])

    def test_search_non_criterion_raises(self) -> None:
        with self.assertRaises(TypeError):
            self.repo.search("not a criterion")  # type: ignore[arg-type]

    def test_clear_empties_repository(self) -> None:
        self.repo.clear()
        self.assertEqual(len(self.repo), 0)
        self.assertEqual(self.repo.all(), [])


class TestPIRRepositoryFromIterable(unittest.TestCase):
    """Functionality: from_iterable classmethod builds a repo from a
    sequence of PIRs."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_from_iterable(self) -> None:
        pirs = [PlainText(text="a"), PlainText(text="b")]
        repo = PIRRepository.from_iterable(pirs)
        self.assertEqual(len(repo), 2)
        self.assertIn(pirs[0].id, repo)
        self.assertIn(pirs[1].id, repo)


if __name__ == "__main__":
    unittest.main()
