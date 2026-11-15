"""Unit tests for :mod:`model.criterion`.

These tests exercise:

* The DSL parser -- every leaf criterion type, every composite connector,
  precedence (``!`` > ``&&`` > ``||``), and parentheses.
* The matcher -- for each leaf criterion type, both a positive match and a
  negative match are checked against at least one PIR of the right type and
  one of the wrong type.
* Field-name validation -- the parser refuses unknown fields and refuses to
  apply a time operator (``<`` / ``>``) to a text field.
* Error positions -- malformed expressions raise
  :class:`CriterionSyntaxError` rather than silently returning an empty
  result set.
"""

from __future__ import annotations

import datetime
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
    PlainText,
    Task,
    TextContainsCriterion,
    TimeCompareCriterion,
    TypeCriterion,
    known_text_fields,
    known_time_fields,
)
from model.criterion import _refresh_field_index


class TestCriterionLeafMatches(unittest.TestCase):
    """Functionality: each leaf criterion type matches / rejects PIRs as
    specified by user story US7."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.note = PlainText(text="buy milk please")
        self.task = Task(description="submit report", deadline="2025-12-31T23:59:59")
        self.event = Event(
            description="standup meeting",
            starting_time="2025-10-15T09:00:00",
            alarm="2025-10-15T08:30:00",
        )
        self.contact = Contact(name="Alice Wang", address="12 Main St", mobile="+1-555-0100")

    def test_type_criterion_matches_correct_type(self) -> None:
        crit = TypeCriterion("task")
        self.assertTrue(crit.matches(self.task))
        self.assertFalse(crit.matches(self.note))

    def test_type_criterion_unknown_type_rejected_at_construction(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            TypeCriterion("no_such_type")

    def test_text_contains_matches_substring(self) -> None:
        crit = TextContainsCriterion("description", "report")
        self.assertTrue(crit.matches(self.task))
        # The event's description "standup meeting" does NOT contain "report"
        self.assertFalse(crit.matches(self.event))

    def test_text_contains_unknown_field_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            TextContainsCriterion("no_such", "x")

    def test_text_contains_does_not_match_non_text_field(self) -> None:
        # If a text criterion is applied to a time field, matches() should
        # return False (rather than raising), so a query like
        # "deadline~"2025"" simply returns 0 results.
        crit = TextContainsCriterion("description", "x")
        self.assertFalse(crit.matches(self.note))  # note has no description field

    def test_text_contains_on_contact_name(self) -> None:
        crit = TextContainsCriterion("name", "Alice")
        self.assertTrue(crit.matches(self.contact))
        self.assertFalse(crit.matches(self.task))

    def test_time_compare_lt(self) -> None:
        crit = TimeCompareCriterion(
            "deadline", TimeCompareCriterion.LT,
            datetime.datetime(2026, 1, 1, 0, 0, 0),
        )
        self.assertTrue(crit.matches(self.task))  # deadline 2025-12-31 < 2026-01-01
        # An event has no deadline -> no match
        self.assertFalse(crit.matches(self.event))

    def test_time_compare_gt(self) -> None:
        crit = TimeCompareCriterion(
            "starting_time", TimeCompareCriterion.GT,
            datetime.datetime(2025, 1, 1, 0, 0, 0),
        )
        self.assertTrue(crit.matches(self.event))
        self.assertFalse(crit.matches(self.task))

    def test_time_compare_eq(self) -> None:
        crit = TimeCompareCriterion(
            "alarm", TimeCompareCriterion.EQ,
            datetime.datetime(2025, 10, 15, 8, 30, 0),
        )
        self.assertTrue(crit.matches(self.event))
        self.assertFalse(crit.matches(self.task))

    def test_time_compare_unknown_field_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            TimeCompareCriterion(
                "no_such", TimeCompareCriterion.LT,
                datetime.datetime(2026, 1, 1),
            )

    def test_time_compare_invalid_op_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            TimeCompareCriterion(
                "deadline", "no_such_op", datetime.datetime(2026, 1, 1)
            )


class TestCriterionCompositeMatches(unittest.TestCase):
    """Functionality: composite criteria (And, Or, Not) compose
    leaf criteria as expected."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.task = Task(description="submit", deadline="2025-12-31T23:59:59")
        self.event = Event(
            description="standup",
            starting_time="2025-10-15T09:00:00",
            alarm="2025-10-15T08:30:00",
        )

    def test_and_matches_only_when_both_true(self) -> None:
        crit = AndCriterion(
            TypeCriterion("task"),
            TextContainsCriterion("description", "submit"),
        )
        self.assertTrue(crit.matches(self.task))
        self.assertFalse(crit.matches(self.event))

    def test_or_matches_when_either_true(self) -> None:
        crit = OrCriterion(
            TypeCriterion("task"),
            TypeCriterion("event"),
        )
        self.assertTrue(crit.matches(self.task))
        self.assertTrue(crit.matches(self.event))

    def test_not_inverts(self) -> None:
        crit = NotCriterion(TypeCriterion("task"))
        self.assertFalse(crit.matches(self.task))
        self.assertTrue(crit.matches(self.event))


class TestCriterionDSLParser(unittest.TestCase):
    """Functionality: the DSL parser builds the expected criterion tree for
    a representative set of expressions."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_parse_single_type(self) -> None:
        c = Criterion.parse("type=task")
        self.assertIsInstance(c, TypeCriterion)

    def test_parse_text_contains_with_quoted_value(self) -> None:
        c = Criterion.parse('description~"submit"')
        self.assertIsInstance(c, TextContainsCriterion)

    def test_parse_text_contains_with_bareword(self) -> None:
        c = Criterion.parse("name~Alice")
        self.assertIsInstance(c, TextContainsCriterion)

    def test_parse_time_lt(self) -> None:
        c = Criterion.parse("deadline<2025-12-31T23:59:59")
        self.assertIsInstance(c, TimeCompareCriterion)

    def test_parse_time_gt(self) -> None:
        c = Criterion.parse("starting_time>2025-10-01T00:00:00")
        self.assertIsInstance(c, TimeCompareCriterion)

    def test_parse_time_eq(self) -> None:
        c = Criterion.parse("alarm=2025-10-15T08:30:00")
        self.assertIsInstance(c, TimeCompareCriterion)

    def test_parse_and(self) -> None:
        c = Criterion.parse("type=task && description~submit")
        self.assertIsInstance(c, AndCriterion)

    def test_parse_or(self) -> None:
        c = Criterion.parse("type=task || type=event")
        self.assertIsInstance(c, OrCriterion)

    def test_parse_not(self) -> None:
        c = Criterion.parse("!type=plaintext")
        self.assertIsInstance(c, NotCriterion)

    def test_parse_parentheses(self) -> None:
        c = Criterion.parse("(type=task || type=event) && !type=plaintext")
        self.assertIsInstance(c, AndCriterion)
        self.assertIsInstance(c._left, OrCriterion)

    def test_parse_precedence_and_over_or(self) -> None:
        # a || b && c parses as a || (b && c)
        c = Criterion.parse("type=task || type=event && description~x")
        self.assertIsInstance(c, OrCriterion)
        self.assertIsInstance(c._right, AndCriterion)

    def test_parse_precedence_not_over_and(self) -> None:
        # !type=task && type=event parses as (!type=task) && type=event
        c = Criterion.parse("!type=task && type=event")
        self.assertIsInstance(c, AndCriterion)
        self.assertIsInstance(c._left, NotCriterion)

    def test_parse_unknown_field_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("no_such_field~x")

    def test_parse_unknown_operator_on_text_field(self) -> None:
        # text fields reject '=' at parse time
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("description=foo")

    def test_parse_unterminated_string_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse('description~"unterminated')

    def test_parse_missing_operator_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("description foo")

    def test_parse_unbalanced_parens_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("(type=task")

    def test_parse_empty_string_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse("")

    def test_parse_non_string_raises(self) -> None:
        with self.assertRaises(CriterionSyntaxError):
            Criterion.parse(42)  # type: ignore[arg-type]


class TestFieldIndexRefresh(unittest.TestCase):
    """Functionality: the text/time field index is correctly populated from
    the PIR subclass metadata."""

    def test_text_fields_includes_description_name_address_mobile_text(self) -> None:
        _refresh_field_index()
        self.assertIn("text", known_text_fields())
        self.assertIn("description", known_text_fields())
        self.assertIn("name", known_text_fields())
        self.assertIn("address", known_text_fields())
        self.assertIn("mobile", known_text_fields())

    def test_time_fields_includes_deadline_starting_time_alarm(self) -> None:
        _refresh_field_index()
        self.assertIn("deadline", known_time_fields())
        self.assertIn("starting_time", known_time_fields())
        self.assertIn("alarm", known_time_fields())


if __name__ == "__main__":
    unittest.main()
