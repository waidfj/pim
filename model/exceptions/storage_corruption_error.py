from __future__ import annotations

from .pim_model_error import PIMModelError


class StorageCorruptionError(PIMModelError):
    """Raised when a ``.pim`` file cannot be parsed or its contents cannot be
    rehydrated into PIR objects."""

    def __init__(self, path: str, detail: str):
        super().__init__(f"Corrupt .pim file {path!r}: {detail}")
        self.path = path
        self.detail = detail
