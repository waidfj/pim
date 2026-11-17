"""Controller package -- PIM system interaction layer.

The controller is the place where the user's textual commands are turned
into method calls on the :class:`model.PIRRepository`.  It owns:

* :class:`controller.parser.CommandTokenizer` -- turns a single input line
  into tokens (handling quoted strings, key=value pairs, etc.);
* :class:`controller.commands.CommandDispatcher` -- maps a parsed command
  to the appropriate handler; each handler returns a string that the
  controller writes to the active :class:`view.Reporter`;
* :class:`controller.cli.REPL` -- the read-eval-print loop itself.

Everything in this package is allowed to import from ``model`` and
``view``, but ``model`` must never import from here.  This is the
Model-View-Controller dependency rule.
"""

from .cli import REPL
from .commands import CommandDispatcher
from .parsed_command import ParsedCommand
from .parser import CommandTokenizer, ParsedCommand, TokenizerError

__all__ = [
    "REPL",
    "CommandDispatcher",
    "CommandTokenizer",
    "ParsedCommand",
    "TokenizerError",
]
