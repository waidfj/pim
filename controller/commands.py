"""Command dispatcher for the PIM REPL.

Each verb recognised by the REPL has a corresponding handler method on
:class:`CommandDispatcher`.  A handler takes a
:class:`ParsedCommand` and returns a string (the response the REPL should
print).  All errors are caught here and rendered as ``ERROR: ...`` so the
REPL never has to deal with exceptions itself.

Supported verbs (see :data:`CommandDispatcher.KNOWN_VERBS`):

    create, list, show, update, delete, search, save, load, clear,
    fields, help, exit

The dispatcher owns a single :class:`PIRRepository`; the CLI is the only
place where state lives, which keeps the rest of the system stateless and
easy to test.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

from model import (
    Criterion,
    PIMModelError,
    PIMStorage,
    PIRRepository,
)
from model.pir import Contact, Event, PlainText, Task
from model.exceptions import (
    UnknownFieldError,
)

from .parser import ParsedCommand, TokenizerError
from view import Formatter


# Type alias for handler functions
Handler = Callable[["CommandDispatcher", ParsedCommand], str]


class CommandDispatcher:
    """Dispatches parsed commands to handlers, owns the active repository."""

    KNOWN_VERBS: tuple = (
        "create", "list", "show", "update", "delete", "search",
        "save", "load", "clear", "fields", "help", "exit",
    )

    # The four concrete PIR classes used by the ``create`` command.
    # Defined as a class-level constant so the user manual can quote the same
    # set without drifting.
    PIR_CLASSES: Dict[str, type] = {
        "plaintext": PlainText,
        "task": Task,
        "event": Event,
        "contact": Contact,
    }

    def __init__(self, repository: Optional[PIRRepository] = None) -> None:
        self._repo = repository if repository is not None else PIRRepository()
        self._handlers: Dict[str, Handler] = {
            "create": self._cmd_create,
            "list": self._cmd_list,
            "show": self._cmd_show,
            "update": self._cmd_update,
            "delete": self._cmd_delete,
            "search": self._cmd_search,
            "save": self._cmd_save,
            "load": self._cmd_load,
            "clear": self._cmd_clear,
            "fields": self._cmd_fields,
            "help": self._cmd_help,
            "exit": self._cmd_exit,
        }

    # -- public access ---------------------------------------------------
    @property
    def repository(self) -> PIRRepository:
        return self._repo

    def dispatch(self, command: ParsedCommand) -> str:
        """Route ``command`` to its handler and return the response string."""
        verb = command.verb
        if verb == "":
            return ""  # blank line, ignore
        handler = self._handlers.get(verb)
        if handler is None:
            return Formatter.format_error(
                f"Unknown command '{verb}'. Type 'help' for usage."
            )
        try:
            return handler(command)
        except PIMModelError as exc:
            return Formatter.format_error(str(exc))
        except TokenizerError as exc:
            return Formatter.format_error(str(exc))
        except ValueError as exc:
            return Formatter.format_error(str(exc))

    # -- handler implementations ----------------------------------------
    def _cmd_create(self, command: ParsedCommand) -> str:
        if not command.positionals:
            raise ValueError(
                "Usage: create <type> <field1>=<value1> <field2>=<value2> ..."
            )
        type_name = command.positionals[0].lower()
        if type_name not in self.PIR_CLASSES:
            raise ValueError(
                f"Unknown PIR type '{type_name}'. "
                f"Valid types: {sorted(self.PIR_CLASSES)}"
            )
        # Build the PIR from the kwargs in declaration order
        cls = self.PIR_CLASSES[type_name]
        field_names = cls.field_names()
        kwargs = command.kwargs
        # Reject extra kwargs we don't understand
        for key in kwargs:
            if key not in field_names:
                raise UnknownFieldError(key)
        # All required fields must be supplied.  For this implementation,
        # every field of every PIR type is required at creation time -- a
        # sensible simplification for a personal-info system.
        missing = [f for f in field_names if f not in kwargs]
        if missing:
            raise ValueError(
                f"Missing required field(s) for {type_name}: {missing}. "
                f"Required fields: {list(field_names)}"
            )
        pir = cls(**{f: kwargs[f] for f in field_names})
        self._repo.add(pir)
        return Formatter.format_info(
            f"Created {cls.__name__} #{pir.id}."
        ) + "\n" + Formatter.format_pir(pir)

    def _cmd_list(self, command: ParsedCommand) -> str:
        if command.positionals or command.kwargs:
            raise ValueError("'list' takes no arguments")
        pirs = self._repo.all()
        return Formatter.format_pir_list(pirs)

    def _cmd_show(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1:
            raise ValueError("Usage: show <id>")
        try:
            pir_id = int(command.positionals[0])
        except ValueError:
            raise ValueError(f"Invalid id '{command.positionals[0]}'; must be an integer")
        pir = self._repo.get(pir_id)
        return Formatter.format_pir(pir)

    def _cmd_update(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1 or len(command.kwargs) != 1:
            raise ValueError(
                "Usage: update <id> <field>=<value>  "
                "(only one field may be updated at a time)"
            )
        try:
            pir_id = int(command.positionals[0])
        except ValueError:
            raise ValueError(
                f"Invalid id '{command.positionals[0]}'; must be an integer"
            )
        ((field, value),) = command.kwargs.items()
        pir = self._repo.update(pir_id, field, value)
        return Formatter.format_info(f"Updated PIR #{pir.id}.") + "\n" + Formatter.format_pir(pir)

    def _cmd_delete(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1:
            raise ValueError("Usage: delete <id>")
        try:
            pir_id = int(command.positionals[0])
        except ValueError:
            raise ValueError(
                f"Invalid id '{command.positionals[0]}'; must be an integer"
            )
        removed = self._repo.remove(pir_id)
        return Formatter.format_info(
            f"Deleted {removed.__class__.__name__} #{pir_id}."
        )

    def _cmd_search(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1 or command.kwargs:
            raise ValueError(
                'Usage: search "<criterion>"  '
                "(wrap the criterion in double quotes)"
            )
        raw_criterion = command.positionals[0]
        criterion = Criterion.parse(raw_criterion)
        matches = self._repo.search(criterion)
        lines = [Formatter.format_count(len(matches))]
        if matches:
            lines.append(Formatter.format_pir_list(matches))
        return "\n".join(lines)

    def _cmd_save(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1 or command.kwargs:
            raise ValueError("Usage: save <file.pim>")
        path = command.positionals[0]
        PIMStorage.save(self._repo, path)
        return Formatter.format_info(
            f"Saved {len(self._repo)} PIR(s) to {path!r}."
        )

    def _cmd_load(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1 or command.kwargs:
            raise ValueError("Usage: load <file.pim>")
        path = command.positionals[0]
        before = len(self._repo)
        PIMStorage.load(self._repo, path)
        after = len(self._repo)
        return Formatter.format_info(
            f"Loaded {after - before} new PIR(s) from {path!r} "
            f"(repository now has {after})."
        )

    def _cmd_clear(self, command: ParsedCommand) -> str:
        if command.positionals or command.kwargs:
            raise ValueError("'clear' takes no arguments")
        n = len(self._repo)
        self._repo.clear()
        return Formatter.format_info(f"Cleared repository (removed {n} PIR(s)).")

    def _cmd_fields(self, command: ParsedCommand) -> str:
        if len(command.positionals) != 1 or command.kwargs:
            raise ValueError("Usage: fields <type>")
        type_name = command.positionals[0].lower()
        if type_name not in self.PIR_CLASSES:
            raise ValueError(
                f"Unknown PIR type '{type_name}'. "
                f"Valid types: {sorted(self.PIR_CLASSES)}"
            )
        cls = self.PIR_CLASSES[type_name]
        kind_map = cls.field_kinds()
        lines = [f"{cls.__name__} fields:"]
        for fname in cls.field_names():
            kind = kind_map.get(fname, "text")
            lines.append(f"  {fname} ({kind})")
        lines.append(
            "  Time fields must use the ISO format YYYY-MM-DDTHH:MM:SS."
        )
        return "\n".join(lines)

    def _cmd_help(self, command: ParsedCommand) -> str:
        if command.positionals or command.kwargs:
            raise ValueError("'help' takes no arguments")
        return Formatter.help_text()

    def _cmd_exit(self, command: ParsedCommand) -> str:
        if command.positionals or command.kwargs:
            raise ValueError("'exit' takes no arguments")
        return "__EXIT__"  # sentinel handled by the REPL
