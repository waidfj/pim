from __future__ import annotations

from .pim_model_error import PIMModelError


class InvalidFileExtensionError(PIMModelError):
    """Raised when a file path used for save/load does not end in ``.pim``."""

    def __init__(self, path: str):
        super().__init__(
            f"File path must end with '.pim', got: {path!r}"
        )
        self.path = path
