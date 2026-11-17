from __future__ import annotations

from typing import List
from ..exceptions import CriterionSyntaxError

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
