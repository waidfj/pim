from __future__ import annotations

from typing import List
from ..exceptions import CriterionSyntaxError, InvalidFieldValueError
from ..pir import parse_datetime
from .base import Criterion
from .composite import AndCriterion, NotCriterion, OrCriterion
from .field_index import _TEXT_FIELDS, _TIME_FIELDS, known_fields
from .text_criterion import TextContainsCriterion
from .time_criterion import TimeCompareCriterion
from .tokenizer import (
    _TOK_AND,
    _TOK_BARE,
    _TOK_END,
    _TOK_EQ,
    _TOK_GT,
    _TOK_IDENT,
    _TOK_LPAREN,
    _TOK_LT,
    _TOK_NOT,
    _TOK_OR,
    _TOK_RPAREN,
    _TOK_STRING,
    _TOK_TILDE,
    _Token,
)
from .type_criterion import TypeCriterion

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
