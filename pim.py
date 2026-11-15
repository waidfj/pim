#!/usr/bin/env python3
"""PIM -- Personal Information Manager.

Entry point for the command-line interface.  Run with::

    python3 pim.py

The system boots into an interactive REPL; type ``help`` for the list of
commands and ``exit`` (or press Ctrl-D) to quit.

The entry point is intentionally tiny: it just wires together the
:class:`controller.cli.REPL` and runs it.  All the actual behaviour lives in
the model, view and controller packages, in line with the
Model-View-Controller architectural pattern.
"""

from __future__ import annotations

import sys

from controller import REPL
from controller.commands import CommandDispatcher
from view import PrintReporter


def main(argv=None) -> int:
    """Program entry point.

    Returns the process exit status so tests can call it and inspect the
    code.  ``argv`` is accepted for symmetry with ``int main(int argc,
    char** argv)`` in C; it is currently unused because the REPL reads
    configuration interactively, but it lets future options (e.g. ``--no-prompt``)
    slot in without rewriting the entry point.
    """
    if argv is None:
        argv = sys.argv[1:]
    dispatcher = CommandDispatcher()
    reporter = PrintReporter()
    repl = REPL(dispatcher=dispatcher, reporter=reporter)
    return repl.run()


if __name__ == "__main__":
    sys.exit(main())
