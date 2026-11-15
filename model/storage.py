"""Persistence layer for the PIM system.

A ``.pim`` file is a UTF-8 JSON document whose top-level structure is::

    {
        "version": "1.0",
        "pirs": [
            {"id": 1, "type": "plaintext", "text": "..."},
            {"id": 2, "type": "task", "description": "...",
             "deadline": "2025-12-31T23:59:59"},
            ...
        ]
    }

The model only depends on :mod:`json` from the standard library.  Loading
rehydrates PIRs via :meth:`model.pir.PIR.from_dict`, which dispatches on the
``type`` field and raises :class:`UnknownPIRTypeError` for unrecognised
types (forward compatibility).  Every loaded PIR's id bumps the global
counter so the next freshly-created record won't collide with a restored one.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from .exceptions import (
    InvalidFileExtensionError,
    StorageCorruptionError,
)
from .pir import PIR

if TYPE_CHECKING:  # pragma: no cover
    from .repository import PIRRepository


# Bumped whenever the on-disk layout changes.  Loader refuses version it
# doesn't understand so we don't silently mis-read a future format.
_FILE_FORMAT_VERSION = "1.0"


class PIMStorage:
    """Static helpers for saving/loading a :class:`PIRRepository` to/from a
    ``.pim`` file.

    The class is intentionally stateless; the file is the only persisted
    state and the repository is the only in-memory state.  This keeps the
    dependency direction obvious (storage depends on repository, never the
    other way around) and means a single :class:`PIMStorage` instance can be
    shared across multiple repositories if needed.
    """

    @staticmethod
    def save(repository: "PIRRepository", file_path: str) -> None:
        """Serialise every PIR in ``repository`` to ``file_path`` as JSON.

        Raises:
            InvalidFileExtensionError: if ``file_path`` does not end in
                ``.pim``.
            OSError: if the file cannot be written.
        """
        PIMStorage._validate_extension(file_path)
        data = {
            "version": _FILE_FORMAT_VERSION,
            "pirs": [pir.to_dict() for pir in repository.all()],
        }
        # Atomic-ish write: write to a temp file then rename.  Using os.replace
        # avoids losing the original file if writing fails partway through.
        tmp_path = file_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_path, file_path)

    @staticmethod
    def load(repository: "PIRRepository", file_path: str) -> None:
        """Load PIRs from ``file_path`` into ``repository``.

        Existing PIRs in the repository are NOT cleared first; the caller
        can call :meth:`PIRRepository.clear` if they want a fresh load.  This
        allows incremental loading from multiple files if a user wants to
        merge records.

        Raises:
            InvalidFileExtensionError: if the path does not end in ``.pim``.
            StorageCorruptionError: if the file cannot be parsed as JSON, is
                missing required keys, or refers to an unknown PIR type.
        """
        PIMStorage._validate_extension(file_path)
        if not os.path.exists(file_path):
            raise StorageCorruptionError(file_path, "file does not exist")
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageCorruptionError(file_path, str(exc)) from exc
        if not isinstance(data, dict):
            raise StorageCorruptionError(
                file_path, "top-level value is not an object"
            )
        version = data.get("version")
        if version != _FILE_FORMAT_VERSION:
            raise StorageCorruptionError(
                file_path,
                f"unsupported file format version: {version!r} "
                f"(expected {_FILE_FORMAT_VERSION!r})",
            )
        pir_list = data.get("pirs")
        if not isinstance(pir_list, list):
            raise StorageCorruptionError(
                file_path, "'pirs' must be a list"
            )
        for entry in pir_list:
            if not isinstance(entry, dict):
                raise StorageCorruptionError(
                    file_path, f"PIR entry is not an object: {entry!r}"
                )
            try:
                pir = PIR.from_dict(entry)
                repository.add(pir)
            except StorageCorruptionError:
                raise
            except Exception as exc:
                raise StorageCorruptionError(
                    file_path, f"failed to load PIR {entry!r}: {exc}"
                ) from exc

    @staticmethod
    def _validate_extension(file_path: str) -> None:
        if not file_path.endswith(".pim"):
            raise InvalidFileExtensionError(file_path)
