"""Command tokenizer for the PIM REPL.

Splits an input line like::

    create task description="Submit report" deadline=2025-12-31T23:59:59

into a structured :class:`ParsedCommand` with:

* ``verb`` -- the leading verb (``create``, ``list``, ``show``, ...)
* ``positionals`` -- bare positional arguments (e.g. ``3`` for ``show 3``)
* ``kwargs`` -- a dict of ``key=value`` pairs (e.g.
  ``{"description": "Submit report", "deadline": "2025-12-31T23:59:59"}``)

Supported token forms:

* ``word`` -- bareword, becomes either the verb or a positional
* ``key=value`` -- keyword argument, where ``value`` may be quoted
* ``"quoted string"`` -- a positional argument that contains spaces; quotes
  are stripped when forming the value

Quotes inside a bareword are *not* stripped, and there are no escape
sequences: the language is intentionally minimal so the user manual can
describe it on one page.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .parsed_command import ParsedCommand


class TokenizerError(ValueError):
    """Raised when the input line cannot be tokenised (e.g. an unterminated
    quoted string)."""


class CommandTokenizer:
    """Stateless tokenizer; only the :meth:`tokenize` classmethod is
    public."""

    @classmethod
    def tokenize(cls, line: str) -> ParsedCommand:
        """Parse ``line`` into a :class:`ParsedCommand`.

        Raises :class:`TokenizerError` on malformed input.
        """
        verb: str = ""
        positionals: List[str] = []
        kwargs: Dict[str, str] = {}
        i = 0
        n = len(line)
        # Skip leading whitespace
        while i < n and line[i].isspace():
            i += 1
        # Read verb (must be a bareword, no = sign, no quotes)
        while i < n and not line[i].isspace():
            ch = line[i]
            if ch == "=":
                raise TokenizerError(
                    "Unexpected '=' while reading verb; the verb must come first"
                )
            if ch == '"':
                raise TokenizerError(
                    "Unexpected '\"' while reading verb; the verb must be a bareword"
                )
            i += 1
        verb = line[:i].strip()
        if not verb:
            return ParsedCommand("", positionals, kwargs, line)

        # Now read positionals and kwargs
        while i < n:
            # Skip whitespace
            while i < n and line[i].isspace():
                i += 1
            if i >= n:
                break

            # Quoted string -> positional
            if line[i] == '"':
                value, i = cls._read_quoted(line, i)
                positionals.append(value)
                continue

            # Bareword or key=value -- read the leading identifier, then
            # decide whether an '=' follows to disambiguate.
            j = i
            while j < n and not line[j].isspace() and line[j] != '=':
                if line[j] == '"':
                    raise TokenizerError(
                        "Unexpected '\"' in the middle of a bareword; "
                        "wrap the whole value in quotes instead"
                    )
                j += 1

            # key=value form
            if j < n and line[j] == '=':
                key = line[i:j]
                if not key:
                    raise TokenizerError(
                        "Missing key in key=value token"
                    )
                # Skip '='
                k = j + 1
                # Value may be quoted, in which case read with _read_quoted
                if k < n and line[k] == '"':
                    value, k = cls._read_quoted(line, k)
                else:
                    # Bareword value: read until whitespace
                    value_start = k
                    while k < n and not line[k].isspace():
                        k += 1
                    value = line[value_start:k]
                kwargs[key] = value
                i = k
                continue

            # Plain bareword positional
            token = line[i:j]
            i = j
            positionals.append(token)

        return ParsedCommand(verb, positionals, kwargs, line)

    @staticmethod
    def _read_quoted(line: str, start: int) -> Tuple[str, int]:
        """Read a quoted string starting at index ``start`` (which must point
        at the opening ``\"``).  Returns ``(value, end_index)`` where the
        value excludes the surrounding quotes and ``end_index`` points just
        past the closing quote."""
        assert line[start] == '"'
        i = start + 1
        n = len(line)
        buf = []
        while i < n and line[i] != '"':
            buf.append(line[i])
            i += 1
        if i >= n:
            raise TokenizerError(
                f"Unterminated quoted string starting at column {start + 1}"
            )
        return "".join(buf), i + 1
