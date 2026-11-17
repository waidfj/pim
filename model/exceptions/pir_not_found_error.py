from __future__ import annotations

from .pim_model_error import PIMModelError


class PIRNotFoundError(PIMModelError):
    """Raised when a PIR with a given id cannot be located in the repository."""

    def __init__(self, pir_id: int):
        super().__init__(f"No PIR with id {pir_id}")
        self.pir_id = pir_id
