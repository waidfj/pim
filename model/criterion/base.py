from __future__ import annotations

from ..exceptions import CriterionSyntaxError
from ..pir import PIR

class Criterion:
    """Abstract base class for all search criteria.

    Every concrete criterion implements :meth:`matches`, which takes a single
    :class:`PIR` and returns ``True``/``False``.  The CLI is free to compose
    criteria programmatically too; the DSL is just a thin textual front-end.
    """

    def matches(self, pir: PIR) -> bool:  # pragma: no cover - abstract
        raise NotImplementedError

    @classmethod
    def parse(cls, expression: str) -> "Criterion":
        from .parser import _CriterionParser
        from .tokenizer import _tokenize
        
        """Parse a criterion DSL string into a :class:`Criterion` tree."""
        if not isinstance(expression, str):
            raise CriterionSyntaxError("expression must be a string")
        tokens = _tokenize(expression)
        parser = _CriterionParser(tokens, expression)
        result = parser.parse_expression()
        parser.expect_end()
        return result

    # Display ------------------------------------------------------------
    def __str__(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

from .parser import _CriterionParser
from .tokenizer import _tokenize
