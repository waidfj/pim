"""Read-Eval-Print Loop for the PIM system.

The REPL owns one :class:`CommandDispatcher` and one :class:`Reporter`.
On each iteration it:

1. reads a line from the input stream (defaults to ``sys.stdin``);
2. tokenises and dispatches it via the dispatcher;
3. writes the response to the reporter.

If the dispatcher returns the sentinel ``"__EXIT__"`` string, the loop
terminates.  Blank lines and the comment marker ``#`` are silently ignored.

A user can also pre-feed commands via a here-document or a pipe; the REPL
exits when input is exhausted, which makes the system scriptable for
demos and tests.
"""

from __future__ import annotations

import sys
from typing import IO, Optional

from view import Formatter, PrintReporter, Reporter
from .commands import CommandDispatcher
from .parser import CommandTokenizer, TokenizerError


# The REPL reads from any text stream; this lets tests drive it from a
# StringIO instead of from a real terminal.
EXIT_SENTINEL = "__EXIT__"


class REPL:
    """Read-Eval-Print loop.

    The constructor wires together a dispatcher and a reporter; both can be
    swapped at construction time which makes the REPL easy to test in
    isolation.
    """

    PROMPT = "pim> "

    def __init__(
        self,
        dispatcher: Optional[CommandDispatcher] = None,
        reporter: Optional[Reporter] = None,
        input_stream: Optional[IO[str]] = None,
        prompt: Optional[str] = None,
    ) -> None:
        self._dispatcher = dispatcher if dispatcher is not None else CommandDispatcher()
        self._reporter = reporter if reporter is not None else PrintReporter()
        self._input_stream = input_stream if input_stream is not None else sys.stdin
        self._prompt = prompt if prompt is not None else REPL.PROMPT

    # -- public API ------------------------------------------------------
    def run(self) -> int:
        """Run the REPL until EOF or the ``exit`` command.

        Returns an exit status code (0 for clean exit, non-zero on
        unexpected error).  Called by :func:`pim.main`.
        """
        self._reporter.write(Formatter.banner())
        exit_code = 0
        try:
            while True:
                line = self._read_line()
                if line is None:  # EOF
                    break
                response = self._eval(line)
                if response is None:
                    continue
                if response == EXIT_SENTINEL:
                    break
                self._reporter.write(response)
                # Ensure responses end with a newline for tidy output
                if not response.endswith("\n"):
                    self._reporter.write("\n")
        except KeyboardInterrupt:
            self._reporter.write("\n" + Formatter.farewell())
            exit_code = 130  # standard Unix convention for SIGINT
        else:
            self._reporter.write(Formatter.farewell())
        return exit_code

    def eval_one(self, line: str) -> str:
        """Evaluate a single input line and return the dispatcher's response
        (without writing it to the reporter).  Public so tests can drive the
        dispatcher one command at a time and inspect the response."""
        response = self._eval(line)
        if response is None:
            return ""
        if response == EXIT_SENTINEL:
            return Formatter.farewell()
        return response

    # -- internals -------------------------------------------------------
    def _read_line(self) -> Optional[str]:
        # Show a prompt only when stdin looks like a TTY (interactive mode)
        if self._is_interactive():
            self._reporter.write(self._prompt)
        line = self._input_stream.readline()
        if not line:
            return None  # EOF
        return line.rstrip("\n")

    def _eval(self, line: str) -> Optional[str]:
        # Skip blank lines and comments silently
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None
        try:
            command = CommandTokenizer.tokenize(line)
        except TokenizerError as exc:
            return Formatter.format_error(str(exc))
        return self._dispatcher.dispatch(command)

    def _is_interactive(self) -> bool:
        stream = self._input_stream
        # sys.stdin.isatty() exists and works on every supported platform;
        # if for some reason the stream doesn't implement it, default to
        # False (i.e. don't show a prompt) so piping still works.
        try:
            return bool(stream.isatty())
        except (AttributeError, ValueError):  # pragma: no cover - defensive
            return False
