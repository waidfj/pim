"""Search criterion classes and a small DSL for building them.

The model layer exposes a tiny criterion language so that the CLI can accept
a single search string from the user and turn it into a tree of
:class:`Criterion` objects that can be evaluated against any
:class:`model.pir.PIR`.  The language supports:

*   ``type=plaintext``      -- restrict by PIR type
*   ``text~"some string"``  -- a text field contains a substring
*   ``deadline<2025-12-31T23:59:59``  -- a time field is strictly before
*   ``deadline>2025-12-31T23:59:59``  -- a time field is strictly after
*   ``deadline=2025-12-31T23:59:59``   -- a time field is exactly equal
*   ``cond && cond``  -- logical AND
*   ``cond || cond``  -- logical OR
*   ``!cond``         -- logical NOT
*   ``(cond)``        -- grouping

Field names are validated at parse time against the union of the
``field_names()`` of every registered PIR subclass plus the virtual field
``type``; using an unknown field raises :class:`CriterionSyntaxError`.  This
means a typo like ``deadlne<2025-01-01`` fails fast at parse time rather than
silently returning zero matches at evaluation time.
"""

from __future__ import annotations

import datetime
from typing import Any, List, Optional, Tuple

from .exceptions import CriterionSyntaxError, InvalidFieldValueError
from .pir import (
    PIR,
    all_pir_types,
    known_type_names,
    parse_datetime,
)


# ---------------------------------------------------------------------------
# Text field registry -- which fields are textual vs. time-like
# ---------------------------------------------------------------------------
def _build_field_index():
    """Return ``(text_fields, time_fields)`` sets collected across all
    registered PIR subclasses.  ``type`` is a virtual field handled
    separately.  Field kind is taken from each subclass's
    :meth:`PIR.field_kinds` classmethod rather than from default values, so
    that time fields whose default is ``None`` are still classified as time
    fields rather than silently as text fields."""
    text_fields = set()
    time_fields = set()
    for subclass in all_pir_types().values():
        for fname, kind in subclass.field_kinds().items():
            if kind == "time":
                time_fields.add(fname)
            else:
                text_fields.add(fname)
    return text_fields, time_fields


_TEXT_FIELDS: set
_TIME_FIELDS: set


def _refresh_field_index() -> None:
    """(Re)build the global text/time field index.  Called once at import
    time; tests that dynamically register PIR subclasses can call it again."""
    global _TEXT_FIELDS, _TIME_FIELDS
    _TEXT_FIELDS, _TIME_FIELDS = _build_field_index()


_refresh_field_index()


def known_text_fields() -> set:
    return set(_TEXT_FIELDS)


def known_time_fields() -> set:
    return set(_TIME_FIELDS)


def known_fields() -> set:
    return _TEXT_FIELDS | _TIME_FIELDS | {"type"}


# ---------------------------------------------------------------------------
# Abstract criterion
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Leaf criteria
# ---------------------------------------------------------------------------
class TypeCriterion(Criterion):
    """Matches PIRs whose canonical type name equals ``type_name``."""

    def __init__(self, type_name: str) -> None:
        if type_name not in known_type_names():
            raise CriterionSyntaxError(
                f"Unknown PIR type '{type_name}'. "
                f"Known types: {sorted(known_type_names())}"
            )
        self._type_name = type_name

    def matches(self, pir: PIR) -> bool:
        return pir.get_type() == self._type_name

    def __str__(self) -> str:
        return f"type={self._type_name}"


class TextContainsCriterion(Criterion):
    """Matches PIRs whose ``field_name`` is a string that contains
    ``substring`` (case-sensitive, substring anywhere in the value)."""

    def __init__(self, field_name: str, substring: str) -> None:
        if field_name not in _TEXT_FIELDS:
            raise CriterionSyntaxError(
                f"'{field_name}' is not a text field. "
                f"Known text fields: {sorted(_TEXT_FIELDS)}"
            )
        if not isinstance(substring, str):
            raise CriterionSyntaxError("text substring must be a string")
        self._field_name = field_name
        self._substring = substring

    def matches(self, pir: PIR) -> bool:
        try:
            value = pir.get_field(self._field_name)
        except Exception:
            return False
        if not isinstance(value, str):
            return False
        return self._substring in value

    def __str__(self) -> str:
        return f"{self._field_name}~{self._substring!r}"


class TimeCompareCriterion(Criterion):
    """Matches PIRs whose ``field_name`` (a time field) compares to
    ``time_value`` using operator ``<``, ``>`` or ``=``."""

    LT = "<"
    GT = ">"
    EQ = "="
    _OPS = {LT, GT, EQ}

    def __init__(
        self, field_name: str, op: str, time_value: datetime.datetime
    ) -> None:
        if field_name not in _TIME_FIELDS:
            raise CriterionSyntaxError(
                f"'{field_name}' is not a time field. "
                f"Known time fields: {sorted(_TIME_FIELDS)}"
            )
        if op not in self._OPS:
            raise CriterionSyntaxError(
                f"Unknown time operator '{op}'. Use one of {sorted(self._OPS)}"
            )
        if not isinstance(time_value, datetime.datetime):
            raise CriterionSyntaxError("time value must be a datetime")
        self._field_name = field_name
        self._op = op
        self._time_value = time_value

    def matches(self, pir: PIR) -> bool:
        try:
            value = pir.get_field(self._field_name)
        except Exception:
            return False
        if not isinstance(value, datetime.datetime):
            return False
        if self._op == self.LT:
            return value < self._time_value
        if self._op == self.GT:
            return value > self._time_value
        return value == self._time_value

    def __str__(self) -> str:
        from .pir import format_datetime
        return (
            f"{self._field_name}{self._op}"
            f"{format_datetime(self._time_value)}"
        )


# ---------------------------------------------------------------------------
# Composite criteria
# ---------------------------------------------------------------------------
class AndCriterion(Criterion):
    def __init__(self, left: Criterion, right: Criterion) -> None:
        self._left = left
        self._right = right

    def matches(self, pir: PIR) -> bool:
        return self._left.matches(pir) and self._right.matches(pir)

    def __str__(self) -> str:
        return f"({self._left} && {self._right})"


class OrCriterion(Criterion):
    def __init__(self, left: Criterion, right: Criterion) -> None:
        self._left = left
        self._right = right

    def matches(self, pir: PIR) -> bool:
        return self._left.matches(pir) or self._right.matches(pir)

    def __str__(self) -> str:
        return f"({self._left} || {self._right})"


class NotCriterion(Criterion):
    def __init__(self, inner: Criterion) -> None:
        self._inner = inner

    def matches(self, pir: PIR) -> bool:
        return not self._inner.matches(pir)

    def __str__(self) -> str:
        return f"!{self._inner}"


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------
# Token kinds
_TOK_LPAREN = "LPAREN"
_TOK_RPAREN = "RPAREN"
_TOK_AND = "AND"
_TOK_OR = "OR"
_TOK_NOT = "NOT"
_TOK_EQ = "EQ"
_TOK_TILDE = "TILDE"
_TOK_LT = "LT"
_TOK_GT = "GT"
_TOK_IDENT = "IDENT"      # field name
_TOK_STRING = "STRING"    # "quoted value"
_TOK_BARE = "BARE"         # unquoted value (datetime, type, single word)
_TOK_END = "END"


class _Token:
    __slots__ = ("kind", "value", "pos")

    def __init__(self, kind: str, value: str, pos: int) -> None:
        self.kind = kind
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"_Token({self.kind}, {self.value!r}, pos={self.pos})"


def _tokenize(expr: str) -> List[_Token]:
    """Turn a criterion expression into a list of tokens.  Whitespace is
    collapsed except inside quoted strings."""
    tokens: List[_Token] = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "(":
            tokens.append(_Token(_TOK_LPAREN, ch, i))
            i += 1
            continue
        if ch == ")":
            tokens.append(_Token(_TOK_RPAREN, ch, i))
            i += 1
            continue
        if ch == "&" and i + 1 < n and expr[i + 1] == "&":
            tokens.append(_Token(_TOK_AND, "&&", i))
            i += 2
            continue
        if ch == "|" and i + 1 < n and expr[i + 1] == "|":
            tokens.append(_Token(_TOK_OR, "||", i))
            i += 2
            continue
        if ch == "!":
            tokens.append(_Token(_TOK_NOT, "!", i))
            i += 1
            continue
        if ch == "=":
            tokens.append(_Token(_TOK_EQ, "=", i))
            i += 1
            continue
        if ch == "~":
            tokens.append(_Token(_TOK_TILDE, "~", i))
            i += 1
            continue
        if ch == "<":
            tokens.append(_Token(_TOK_LT, "<", i))
            i += 1
            continue
        if ch == ">":
            tokens.append(_Token(_TOK_GT, ">", i))
            i += 1
            continue
        if ch == '"':
            # Quoted string -- read until the matching quote.  Embedded
            # quotes are NOT supported (keep the language minimal).
            j = i + 1
            buf = []
            while j < n and expr[j] != '"':
                buf.append(expr[j])
                j += 1
            if j >= n:
                raise CriterionSyntaxError(
                    "Unterminated string literal", position=i
                )
            tokens.append(_Token(_TOK_STRING, "".join(buf), i))
            i = j + 1
            continue
        # Identifier or bare value -- letters/digits/_/-/./+/:
        # (we accept a generous set so ISO datetimes and phone numbers
        # don't need quoting)
        # Allowed bareword chars: letters/digits (via isalnum) plus
        # underscore, dash, dot, plus, slash, colon.  Colon is needed for
        # ISO datetimes; plus is needed for phone numbers like +1-555-0100.
        _BAREWORD_EXTRA = "_-.+/:"
        if ch.isalnum() or ch in _BAREWORD_EXTRA:
            j = i
            buf = []
            while j < n and (expr[j].isalnum() or expr[j] in _BAREWORD_EXTRA):
                buf.append(expr[j])
                j += 1
            tokens.append(_Token(_TOK_BARE, "".join(buf), i))
            i = j
            continue
        raise CriterionSyntaxError(
            f"Unexpected character {ch!r}", position=i
        )
    tokens.append(_Token(_TOK_END, "", n))
    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------
class _CriterionParser:
    """Recursive-descent parser for the criterion DSL.

    Grammar::

        expr      := or_expr
        or_expr   := and_expr ('||' and_expr)*
        and_expr  := not_expr ('&&' not_expr)*
        not_expr  := '!' not_expr | atom
        atom      := '(' expr ')' | comparison
        comparison:= field op value
        field     := IDENT (must be a known field)
        op        := '=' | '~' | '<' | '>'
        value     := STRING | BARE
    """

    def __init__(self, tokens: List[_Token], original: str) -> None:
        self._tokens = tokens
        self._pos = 0
        self._original = original

    # -- token helpers ---------------------------------------------------
    def _peek(self) -> _Token:
        return self._tokens[self._pos]

    def _advance(self) -> _Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def expect_end(self) -> None:
        if self._peek().kind != _TOK_END:
            tok = self._peek()
            raise CriterionSyntaxError(
                f"Expected end of input, got {tok.kind} ({tok.value!r})",
                position=tok.pos,
            )

    # -- grammar ---------------------------------------------------------
    def parse_expression(self) -> Criterion:
        return self._parse_or()

    def _parse_or(self) -> Criterion:
        left = self._parse_and()
        while self._peek().kind == _TOK_OR:
            self._advance()
            right = self._parse_and()
            left = OrCriterion(left, right)
        return left

    def _parse_and(self) -> Criterion:
        left = self._parse_not()
        while self._peek().kind == _TOK_AND:
            self._advance()
            right = self._parse_not()
            left = AndCriterion(left, right)
        return left

    def _parse_not(self) -> Criterion:
        if self._peek().kind == _TOK_NOT:
            self._advance()
            inner = self._parse_not()
            return NotCriterion(inner)
        return self._parse_atom()

    def _parse_atom(self) -> Criterion:
        tok = self._peek()
        if tok.kind == _TOK_LPAREN:
            self._advance()
            inner = self.parse_expression()
            if self._peek().kind != _TOK_RPAREN:
                raise CriterionSyntaxError(
                    "Expected ')'", position=self._peek().pos
                )
            self._advance()
            return inner
        return self._parse_comparison()

    def _parse_comparison(self) -> Criterion:
        field_tok = self._peek()
        if field_tok.kind not in (_TOK_BARE, _TOK_IDENT):
            raise CriterionSyntaxError(
                f"Expected a field name, got {field_tok.kind} "
                f"({field_tok.value!r})",
                position=field_tok.pos,
            )
        # _TOK_BARE and _TOK_IDENT are the same in this tokenizer
        field_name = field_tok.value
        self._advance()
        op_tok = self._peek()
        if op_tok.kind == _TOK_EQ:
            self._advance()
            value_tok = self._advance()
            value = self._coerce_value(value_tok)
            # '=' is overloaded: type=foo is a type filter, but time=foo is
            # an equality comparison on the time field.
            if field_name == "type":
                return TypeCriterion(value)
            if field_name in _TIME_FIELDS:
                try:
                    dt = parse_datetime(value) if isinstance(value, str) else value
                except InvalidFieldValueError as exc:
                    raise CriterionSyntaxError(
                        f"Invalid datetime for '{field_name}': {value!r}",
                        position=value_tok.pos,
                    ) from exc
                return TimeCompareCriterion(field_name, TimeCompareCriterion.EQ, dt)
            if field_name in _TEXT_FIELDS:
                raise CriterionSyntaxError(
                    f"'=' is not a valid operator for text field "
                    f"'{field_name}'; use '~' for substring contains"
                )
            raise CriterionSyntaxError(
                f"Unknown field '{field_name}'. "
                f"Known fields: {sorted(known_fields())}"
            )
        if op_tok.kind == _TOK_TILDE:
            self._advance()
            value_tok = self._advance()
            value = self._coerce_value(value_tok)
            return TextContainsCriterion(field_name, value)
        if op_tok.kind in (_TOK_LT, _TOK_GT):
            self._advance()
            value_tok = self._advance()
            value = self._coerce_value(value_tok)
            try:
                dt = parse_datetime(value) if isinstance(value, str) else value
            except InvalidFieldValueError as exc:
                raise CriterionSyntaxError(
                    f"Invalid datetime for '{field_name}': {value!r}",
                    position=value_tok.pos,
                ) from exc
            op = TimeCompareCriterion.LT if op_tok.kind == _TOK_LT else TimeCompareCriterion.GT
            return TimeCompareCriterion(field_name, op, dt)
        raise CriterionSyntaxError(
            f"Expected an operator ('=', '~', '<' or '>') after field "
            f"'{field_name}', got {op_tok.kind} ({op_tok.value!r})",
            position=op_tok.pos,
        )

    @staticmethod
    def _coerce_value(tok: _Token) -> str:
        if tok.kind in (_TOK_STRING, _TOK_BARE):
            return tok.value
        raise CriterionSyntaxError(
            f"Expected a value, got {tok.kind} ({tok.value!r})",
            position=tok.pos,
        )


# Public re-exports ----------------------------------------------------------
__all__ = [
    "Criterion",
    "TypeCriterion",
    "TextContainsCriterion",
    "TimeCompareCriterion",
    "AndCriterion",
    "OrCriterion",
    "NotCriterion",
]
