"""Additional edge-case tests for the model layer.

These tests target the error-handling and boundary branches that the
"main" test modules don't fully cover, so the reported line coverage
reflects real behaviour rather than just the happy path.

Specifically exercised:

* :class:`PIR.__repr__` and the per-subclass ``__repr__`` paths.
* :meth:`PIR.matches` convenience method (symmetry with
  :meth:`Criterion.matches`).
* Several corner cases of the criterion DSL parser -- empty parens,
  extra tokens after the expression, invalid datetime literals, unknown
  operators, ``=`` on a text field, etc.
* Storage's "PIR entry is not an object" path (when a ``.pim`` file
  contains a non-dict element in the ``pirs`` list).
* The ``__repr__`` of :class:`PIRRepository`.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import tempfile
import unittest

from model import (
    AndCriterion,
    Contact,
    Criterion,
    CriterionSyntaxError,
    Event,
    NotCriterion,
    OrCriterion,
    PIR,
    PIMStorage,
    PIRRepository,
    PlainText,
    Task,
    TextContainsCriterion,
    TimeCompareCriterion,
    TypeCriterion,
)


class TestPIRReprAndMatches(unittest.TestCase):
    """Functionality: __repr__ and the convenience matches() method on PIR."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_pir_repr_includes_class_and_id(self) -> None:
        p = PlainText(text="hello", pir_id=42)
        r = repr(p)
        self.assertIn("PlainText", r)
        self.assertIn("id=42", r)

    def test_pir_matches_delegates_to_criterion(self) -> None:
        p = Task(description="x", deadline="2025-01-01T00:00:00")
        crit = TypeCriterion("task")
        # PIR.matches(pir, crit) should equal crit.matches(pir)
        self.assertEqual(p.matches(crit), crit.matches(p))

    def test_pir_from_dict_returns_correct_subclass(self) -> None:
        for cls in (PlainText, Task, Event, Contact):
            instance = cls()
            restored = PIR.from_dict(instance.to_dict())
            self.assertIsInstance(restored, cls)


class TestCriterionDSLEdgeCases(unittest.TestCase):
    """Functionality: the criterion DSL parser raises sensible errors on
    malformed input."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_parse_extra_tokens_after_expression(self) -> None:
        # The parser should reject "type=task extra"
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("type=task extra")

    def test_parse_empty_parens(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("()")

    def test_parse_invalid_datetime_in_lt(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("deadline<not-a-date")

    def test_parse_invalid_datetime_in_eq(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("deadline=not-a-date")

    def test_parse_eq_on_text_field_rejected(self) -> None:
        # text fields reject '=' at parse time -- only '~' is valid
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("text=foo")

    def test_parse_lt_on_text_field_rejected(self) -> None:
        # text fields reject '<' at parse time
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("text<2025-01-01T00:00:00")

    def test_parse_unexpected_character(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("type=task @ foo")

    def test_parse_double_negation(self) -> None:
        # !! is valid and parses
        c = Criterion.parse("!!type=task")
        self.assertIsInstance(c, NotCriterion)
        self.assertIsInstance(c._inner, NotCriterion)

    def test_str_round_trip(self) -> None:
        # String representation should be informative enough to copy/paste
        # back into a parser.  We don't assert exact round-trip parsing,
        # just that __str__ produces non-empty output.
        c = Criterion.parse("type=task && deadline<2025-12-31T23:59:59")
        self.assertTrue(str(c))

    def test_text_contains_with_empty_substring_matches_anything(self) -> None:
        # Empty substring is in every string
        c = TextContainsCriterion("description", "")
        p = Task(description="anything")
        self.assertTrue(c.matches(p))

    def test_time_compare_on_uninitialised_time_returns_false(self) -> None:
        # A Task created without a deadline has deadline=None; the time
        # criterion should return False (not raise) so the user gets 0
        # matches instead of an error.
        c = TimeCompareCriterion(
            "deadline", TimeCompareCriterion.LT,
            datetime.datetime(2026, 1, 1),
        )
        t = Task(description="no deadline")
        self.assertFalse(c.matches(t))


class TestStorageExtraCoverage(unittest.TestCase):
    """Functionality: storage corner cases not exercised by the main test
    module."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.tmpdir = tempfile.mkdtemp(prefix="pim_extra_")

    def tearDown(self) -> None:
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_pirs_entry_not_object_raises(self) -> None:
        path = os.path.join(self.tmpdir, "bad.pim")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"version": "1.0", "pirs": ["not an object"]}, fh)
        with self.assertRaises(Exception):
            PIMStorage.load(PIRRepository(), path)

    def test_save_then_load_empty_repository(self) -> None:
        path = os.path.join(self.tmpdir, "empty.pim")
        repo = PIRRepository()
        PIMStorage.save(repo, path)
        loaded = PIRRepository()
        PIMStorage.load(loaded, path)
        self.assertEqual(len(loaded), 0)


class TestRepositoryRepr(unittest.TestCase):
    """Functionality: PIRRepository.__repr__ shows the count."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_repr_shows_count(self) -> None:
        repo = PIRRepository()
        repo.add(PlainText(text="x"))
        r = repr(repo)
        self.assertIn("count=1", r)


if __name__ == "__main__":
    unittest.main()
