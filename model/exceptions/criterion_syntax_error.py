from __future__ import annotations

from .pim_model_error import PIMModelError


class CriterionSyntaxError(PIMModelError):
    """Raised when a search-criterion expression cannot be tokenised or
    parsed."""

    def __init__(self, detail: str, position: int = -1):
        super().__init__(f"Criterion syntax error: {detail}")
        self.detail = detail
        self.position = position
