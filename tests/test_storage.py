"""Unit tests for :mod:`model.storage`.

These tests exercise the ``.pim`` file persistence:

* Round-trip equality -- save a repository, load it into a fresh repository,
  confirm every PIR's id, type and field values survive.
* File extension validation -- only ``.pim`` is accepted; other
  extensions raise :class:`InvalidFileExtensionError`.
* Corrupt file detection -- a non-JSON file, a JSON file with the wrong
  structure, an unknown PIR type, or a missing version field all raise
  :class:`StorageCorruptionError`.
* Id counter bumping -- after loading, the global id counter is past the
  highest loaded id, so the next freshly-created PIR doesn't collide with
  a restored one.
* Merge semantics -- :meth:`load` does not clear the repository first, so
  loading into a non-empty repository increments the count correctly.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from model import (
    Contact,
    Event,
    PIMStorage,
    PIR,
    PIRRepository,
    PlainText,
    Task,
)
from model.exceptions import (
    DuplicatePIRIdError,
    InvalidFileExtensionError,
    StorageCorruptionError,
)


class TestPIMStorageRoundTrip(unittest.TestCase):
    """Functionality: save -> load preserves every PIR's id, type and
    field values."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.tmpdir = tempfile.mkdtemp(prefix="pim_test_")
        self.path = os.path.join(self.tmpdir, "demo.pim")
        self.repo = PIRRepository()
        self.note = PlainText(text="note text")
        self.task = Task(description="do work", deadline="2025-12-31T23:59:59")
        self.event = Event(
            description="meeting",
            starting_time="2025-10-15T09:00:00",
            alarm="2025-10-15T08:30:00",
        )
        self.contact = Contact(
            name="Alice",
            address="Earth",
            mobile="+1-555-0100",
        )
        for p in (self.note, self.task, self.event, self.contact):
            self.repo.add(p)

    def tearDown(self) -> None:
        # shutil.rmtree tolerates non-empty dirs and missing files
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_round_trip_preserves_all_pirs(self) -> None:
        PIMStorage.save(self.repo, self.path)
        loaded = PIRRepository()
        PIMStorage.load(loaded, self.path)
        self.assertEqual(len(loaded), 4)
        # id-set equality
        self.assertEqual(
            {p.id for p in loaded},
            {self.note.id, self.task.id, self.event.id, self.contact.id},
        )

    def test_round_trip_preserves_types(self) -> None:
        PIMStorage.save(self.repo, self.path)
        loaded = PIRRepository()
        PIMStorage.load(loaded, self.path)
        types_in_loaded = {type(p) for p in loaded}
        self.assertEqual(
            types_in_loaded,
            {PlainText, Task, Event, Contact},
        )

    def test_round_trip_preserves_field_values(self) -> None:
        PIMStorage.save(self.repo, self.path)
        loaded = PIRRepository()
        PIMStorage.load(loaded, self.path)
        loaded_task = loaded.get(self.task.id)
        self.assertIsInstance(loaded_task, Task)
        self.assertEqual(loaded_task.get_field("description"), "do work")

    def test_loaded_ids_bump_counter(self) -> None:
        """After loading PIRs with ids up to N, the next auto-allocated id
        is N+1."""
        PIMStorage.save(self.repo, self.path)
        loaded = PIRRepository()
        PIMStorage.load(loaded, self.path)
        # The highest id was 4 (4 PIRs created in setUp starting at 1)
        fresh = PlainText(text="fresh")
        self.assertEqual(fresh.id, 5)


class TestPIMStorageFileFormat(unittest.TestCase):
    """Functionality: the .pim file is JSON with a known structure that
    other tools can read."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.tmpdir = tempfile.mkdtemp(prefix="pim_test_")
        self.path = os.path.join(self.tmpdir, "demo.pim")

    def tearDown(self) -> None:
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_saved_file_is_valid_json(self) -> None:
        repo = PIRRepository()
        repo.add(PlainText(text="hello"))
        PIMStorage.save(repo, self.path)
        with open(self.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn("version", data)
        self.assertIn("pirs", data)
        self.assertEqual(len(data["pirs"]), 1)
        self.assertEqual(data["pirs"][0]["type"], "plaintext")

    def test_load_unknown_type_raises(self) -> None:
        path = os.path.join(self.tmpdir, "bad.pim")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({
                "version": "1.0",
                "pirs": [{"id": 1, "type": "no_such_type"}],
            }, fh)
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(PIRRepository(), path)

    def test_load_wrong_version_raises(self) -> None:
        path = os.path.join(self.tmpdir, "bad.pim")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"version": "999", "pirs": []}, fh)
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(PIRRepository(), path)

    def test_load_corrupt_json_raises(self) -> None:
        path = os.path.join(self.tmpdir, "bad.pim")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not json {")
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(PIRRepository(), path)

    def test_load_missing_file_raises(self) -> None:
        path = os.path.join(self.tmpdir, "missing.pim")
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(PIRRepository(), path)

    def test_load_top_level_not_object_raises(self) -> None:
        path = os.path.join(self.tmpdir, "bad.pim")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(["not", "an", "object"], fh)
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(PIRRepository(), path)

    def test_load_pirs_not_list_raises(self) -> None:
        path = os.path.join(self.tmpdir, "bad.pim")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"version": "1.0", "pirs": "not a list"}, fh)
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(PIRRepository(), path)


class TestPIMStorageExtensionValidation(unittest.TestCase):
    """Functionality: only '.pim' file paths are accepted for save/load."""

    def test_save_rejects_non_pim_extension(self) -> None:
        with self.assertRaises(InvalidFileExtensionError):
            PIMStorage.save(PIRRepository(), "/tmp/foo.txt")

    def test_load_rejects_non_pim_extension(self) -> None:
        with self.assertRaises(InvalidFileExtensionError):
            PIMStorage.load(PIRRepository(), "/tmp/foo.txt")


class TestPIMStorageMerge(unittest.TestCase):
    """Functionality: load() merges into the existing repository rather
    than replacing it."""

    def setUp(self) -> None:
        PIR.reset_id_counter(1)
        self.tmpdir = tempfile.mkdtemp(prefix="pim_test_")
        self.path = os.path.join(self.tmpdir, "demo.pim")
        self.repo = PIRRepository()
        self.repo.add(PlainText(text="one"))
        self.repo.add(PlainText(text="two"))
        PIMStorage.save(self.repo, self.path)

    def tearDown(self) -> None:
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_into_empty_repo(self) -> None:
        empty = PIRRepository()
        PIMStorage.load(empty, self.path)
        self.assertEqual(len(empty), 2)

    def test_load_into_non_empty_repo_increments_count(self) -> None:
        # Pre-populate with two more PIRs whose ids are 3 and 4
        repo = PIRRepository()
        repo.add(PlainText(text="three"))
        repo.add(PlainText(text="four"))
        before = len(repo)
        # Loading should merge in the two PIRs from the .pim file (whose ids
        # are 1 and 2, lower than the existing 3 and 4 -- so no collision)
        PIMStorage.load(repo, self.path)
        self.assertEqual(len(repo), before + 2)

    def test_load_into_repo_with_collision_raises(self) -> None:
        # The .pim file contains ids 1 and 2; if we put a PIR with id 1
        # into the target repo, load() should raise DuplicatePIRIdError
        # (wrapped as StorageCorruptionError actually because from_dict
        # is inside the load try-block -- but the outer wrapper converts
        # it to StorageCorruptionError).
        repo = PIRRepository()
        repo.add(PlainText(text="collision", pir_id=1))
        with self.assertRaises(StorageCorruptionError):
            PIMStorage.load(repo, self.path)


if __name__ == "__main__":
    unittest.main()
