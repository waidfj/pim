"""Unit tests for :mod:`model.pir`.

These tests exercise:

* PIR id allocation -- consecutive ids, id counter bumping past loaded ids,
  and explicit reset for test isolation.
* Field protocol -- :meth:`get_field`, :meth:`set_field`,
  :meth:`field_names`, :meth:`field_kinds` for every concrete subclass.
* Validation -- rejecting non-string text values and non-ISO datetime
  values at construction and via :meth:`set_field`.
* (De)serialisation -- round-trip equality via :meth:`to_dict` /
  :meth:`from_dict`, including the ``type`` field used for dispatch.
* The PIR type registry -- :func:`all_pir_types` returns the four
  expected subclasses, and :func:`known_type_names` returns their
  canonical names in definition order.

Each test method's docstring describes the functionality under test so
readers can map a failure to a requirement without re-reading the
production code.
"""

from __future__ import annotations

import datetime
import unittest

from model import (
    Contact,
    Event,
    PlainText,
    PIR,
    Task,
    all_pir_types,
    format_datetime,
    known_type_names,
    parse_datetime,
)
from model.exceptions import (
    InvalidFieldValueError,
    UnknownFieldError,
    UnknownPIRTypeError,
)


class TestPIRIdAllocation(unittest.TestCase):
    """Functionality: PIR ids are allocated sequentially from a
    process-global counter that bumps past loaded ids."""

    def setUp(self) -> None:
        """Reset the id counter before every test so tests are
        order-independent."""
        PIR.reset_id_counter(1)

    def test_consecutive_ids_for_new_pirs(self) -> None:
        """Newly created PIRs without explicit ids receive 1, 2, 3, ..."""
        a = PlainText(text="a")
        b = PlainText(text="b")
        c = PlainText(text="c")
        self.assertEqual(a.id, 1, "first PIR should get id 1")
        self.assertEqual(b.id, 2, "second PIR should get id 2")
        self.assertEqual(c.id, 3, "third PIR should get id 3")

    def test_explicit_id_does_not_consume_counter(self) -> None:
        """When a PIR is reconstructed with an explicit id, the counter is
        bumped *past* it so the next auto-allocated id doesn't collide."""
        loaded = PlainText(text="loaded", pir_id=10)
        self.assertEqual(loaded.id, 10, "explicit id is preserved")
        fresh = PlainText(text="fresh")
        self.assertEqual(
            fresh.id,
            11,
            "after loading id 10, next auto id should be 11",
        )

    def test_reset_id_counter_can_lower_counter(self) -> None:
        """reset_id_counter can lower the counter for tests."""
        PlainText(text="one")  # consumes id 1
        PlainText(text="two")  # consumes id 2
        PIR.reset_id_counter(1)
        again = PlainText(text="again")
        self.assertEqual(again.id, 1, "counter restarted at 1")


class TestPlainText(unittest.TestCase):
    """Functionality: PlainText PIR exposes a single 'text' field."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_field_names_returns_text_only(self) -> None:
        self.assertEqual(PlainText.field_names(), ("text",))

    def test_field_kinds_text(self) -> None:
        self.assertEqual(PlainText.field_kinds(), {"text": "text"})

    def test_get_field_text(self) -> None:
        p = PlainText(text="hello")
        self.assertEqual(p.get_field("text"), "hello")

    def test_get_field_unknown_raises(self) -> None:
        p = PlainText(text="hello")
        with self.assertRaises(UnknownFieldError) as ctx:
            p.get_field("description")
        self.assertEqual(ctx.exception.field_name, "description")

    def test_set_field_text(self) -> None:
        p = PlainText(text="hello")
        p.set_field("text", "world")
        self.assertEqual(p.get_field("text"), "world")

    def test_set_field_unknown_raises(self) -> None:
        p = PlainText(text="hello")
        with self.assertRaises(UnknownFieldError):
            p.set_field("name", "Alice")

    def test_set_field_invalid_type_raises(self) -> None:
        p = PlainText(text="hello")
        with self.assertRaises(InvalidFieldValueError):
            p.set_field("text", 123)  # not a string

    def test_constructor_rejects_non_string_text(self) -> None:
        with self.assertRaises(InvalidFieldValueError):
            PlainText(text=42)

    def test_to_dict_contains_type_and_text(self) -> None:
        p = PlainText(text="hello", pir_id=7)
        d = p.to_dict()
        self.assertEqual(d, {"id": 7, "type": "plaintext", "text": "hello"})

    def test_from_dict_round_trip(self) -> None:
        original = PlainText(text="hello", pir_id=7)
        d = original.to_dict()
        restored = PIR.from_dict(d)
        self.assertIsInstance(restored, PlainText)
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.get_field("text"), original.get_field("text"))


class TestTask(unittest.TestCase):
    """Functionality: Task exposes description (text) and deadline (time)."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_field_names(self) -> None:
        self.assertEqual(Task.field_names(), ("description", "deadline"))

    def test_field_kinds(self) -> None:
        self.assertEqual(
            Task.field_kinds(),
            {"description": "text", "deadline": "time"},
        )

    def test_get_fields(self) -> None:
        t = Task(description="do", deadline="2025-12-31T23:59:59")
        self.assertEqual(t.get_field("description"), "do")
        self.assertEqual(
            t.get_field("deadline"),
            datetime.datetime(2025, 12, 31, 23, 59, 59),
        )

    def test_unknown_field_raises(self) -> None:
        t = Task(description="do")
        with self.assertRaises(UnknownFieldError):
            t.get_field("starting_time")

    def test_set_deadline_string_is_parsed(self) -> None:
        t = Task(description="do")
        t.set_field("deadline", "2025-01-02T03:04:05")
        self.assertEqual(
            t.get_field("deadline"),
            datetime.datetime(2025, 1, 2, 3, 4, 5),
        )

    def test_set_deadline_invalid_raises(self) -> None:
        t = Task(description="do")
        with self.assertRaises(InvalidFieldValueError):
            t.set_field("deadline", "not-a-date")

    def test_set_deadline_none_clears(self) -> None:
        t = Task(description="do", deadline="2025-01-01T00:00:00")
        t.set_field("deadline", None)
        self.assertIsNone(t.get_field("deadline"))

    def test_to_dict_serialises_deadline_as_string(self) -> None:
        t = Task(description="do", deadline="2025-12-31T23:59:59", pir_id=3)
        d = t.to_dict()
        self.assertEqual(d, {
            "id": 3,
            "type": "task",
            "description": "do",
            "deadline": "2025-12-31T23:59:59",
        })

    def test_from_dict_round_trip(self) -> None:
        t = Task(description="do", deadline="2025-12-31T23:59:59", pir_id=5)
        d = t.to_dict()
        r = PIR.from_dict(d)
        self.assertIsInstance(r, Task)
        self.assertEqual(r.id, t.id)
        self.assertEqual(r.get_field("description"), t.get_field("description"))
        self.assertEqual(r.get_field("deadline"), t.get_field("deadline"))


class TestEvent(unittest.TestCase):
    """Functionality: Event exposes description, starting_time, alarm."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_field_names(self) -> None:
        self.assertEqual(
            Event.field_names(),
            ("description", "starting_time", "alarm"),
        )

    def test_field_kinds(self) -> None:
        self.assertEqual(
            Event.field_kinds(),
            {
                "description": "text",
                "starting_time": "time",
                "alarm": "time",
            },
        )

    def test_get_fields(self) -> None:
        e = Event(
            description="m",
            starting_time="2025-10-15T09:00:00",
            alarm="2025-10-15T08:30:00",
        )
        self.assertEqual(e.get_field("description"), "m")
        self.assertEqual(
            e.get_field("starting_time"),
            datetime.datetime(2025, 10, 15, 9, 0, 0),
        )
        self.assertEqual(
            e.get_field("alarm"),
            datetime.datetime(2025, 10, 15, 8, 30, 0),
        )

    def test_set_field_unknown_raises(self) -> None:
        e = Event(description="m")
        with self.assertRaises(UnknownFieldError):
            e.set_field("deadline", "2025-01-01T00:00:00")

    def test_set_field_alarm_with_string(self) -> None:
        e = Event(description="m")
        e.set_field("alarm", "2025-06-01T07:00:00")
        self.assertEqual(
            e.get_field("alarm"),
            datetime.datetime(2025, 6, 1, 7, 0, 0),
        )

    def test_to_dict_with_none_times(self) -> None:
        e = Event(description="m", pir_id=2)
        d = e.to_dict()
        self.assertEqual(d, {
            "id": 2,
            "type": "event",
            "description": "m",
            "starting_time": None,
            "alarm": None,
        })

    def test_from_dict_round_trip(self) -> None:
        e = Event(
            description="m",
            starting_time="2025-10-15T09:00:00",
            alarm="2025-10-15T08:30:00",
            pir_id=8,
        )
        r = PIR.from_dict(e.to_dict())
        self.assertIsInstance(r, Event)
        self.assertEqual(r.id, e.id)
        self.assertEqual(r.get_field("description"), e.get_field("description"))
        self.assertEqual(r.get_field("starting_time"), e.get_field("starting_time"))
        self.assertEqual(r.get_field("alarm"), e.get_field("alarm"))


class TestContact(unittest.TestCase):
    """Functionality: Contact exposes name, address, mobile -- all text."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)

    def test_field_names(self) -> None:
        self.assertEqual(Contact.field_names(), ("name", "address", "mobile"))

    def test_field_kinds_all_text(self) -> None:
        kinds = Contact.field_kinds()
        self.assertEqual(kinds, {
            "name": "text",
            "address": "text",
            "mobile": "text",
        })

    def test_get_and_set_fields(self) -> None:
        c = Contact(name="Alice", address="Here", mobile="+1-555-0100")
        self.assertEqual(c.get_field("name"), "Alice")
        c.set_field("address", "There")
        self.assertEqual(c.get_field("address"), "There")

    def test_unknown_field(self) -> None:
        c = Contact(name="A")
        with self.assertRaises(UnknownFieldError):
            c.set_field("description", "x")

    def test_constructor_rejects_non_string(self) -> None:
        with self.assertRaises(InvalidFieldValueError):
            Contact(name=42)

    def test_to_dict_and_from_dict_round_trip(self) -> None:
        c = Contact(name="Alice", address="Here", mobile="+1-555-0100", pir_id=11)
        d = c.to_dict()
        self.assertEqual(d, {
            "id": 11,
            "type": "contact",
            "name": "Alice",
            "address": "Here",
            "mobile": "+1-555-0100",
        })
        r = PIR.from_dict(d)
        self.assertIsInstance(r, Contact)
        self.assertEqual(r.id, c.id)
        self.assertEqual(r.get_field("name"), c.get_field("name"))
        self.assertEqual(r.get_field("address"), c.get_field("address"))
        self.assertEqual(r.get_field("mobile"), c.get_field("mobile"))


class TestPIRRegistry(unittest.TestCase):
    """Functionality: the PIR type registry exposes all 4 subclasses and
    dispatches :meth:`PIR.from_dict` correctly by ``type``."""

    def test_known_type_names_includes_all_four(self) -> None:
        names = set(known_type_names())
        self.assertEqual(names, {"plaintext", "task", "event", "contact"})

    def test_all_pir_types_returns_classes(self) -> None:
        registry = all_pir_types()
        self.assertIs(registry["plaintext"], PlainText)
        self.assertIs(registry["task"], Task)
        self.assertIs(registry["event"], Event)
        self.assertIs(registry["contact"], Contact)

    def test_from_dict_unknown_type_raises(self) -> None:
        with self.assertRaises(UnknownPIRTypeError):
            PIR.from_dict({"id": 1, "type": "no_such_type"})


class TestDatetimeHelpers(unittest.TestCase):
    """Functionality: parse_datetime and format_datetime are inverse
    operations for the canonical ISO-ish format used throughout the
    system."""

    def test_parse_datetime_valid(self) -> None:
        dt = parse_datetime("2025-12-31T23:59:59")
        self.assertEqual(dt, datetime.datetime(2025, 12, 31, 23, 59, 59))

    def test_parse_datetime_invalid_raises(self) -> None:
        with self.assertRaises(InvalidFieldValueError):
            parse_datetime("2025/12/31 23:59:59")

    def test_parse_datetime_non_string_raises(self) -> None:
        with self.assertRaises(InvalidFieldValueError):
            parse_datetime(20251231)

    def test_format_datetime_round_trip(self) -> None:
        dt = datetime.datetime(2025, 1, 2, 3, 4, 5)
        self.assertEqual(parse_datetime(format_datetime(dt)), dt)


if __name__ == "__main__":
    unittest.main()
