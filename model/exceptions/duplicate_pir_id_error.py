from __future__ import annotations

from .pim_model_error import PIMModelError


class DuplicatePIRIdError(PIMModelError):
    """Raised when an attempt is made to insert a PIR whose id is already
    present in the repository."""

    def __init__(self, pir_id: int):
        super().__init__(f"A PIR with id {pir_id} already exists")
        self.pir_id = pir_id
