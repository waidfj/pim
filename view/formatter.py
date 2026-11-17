"""Output formatting for the PIM CLI."""

from __future__ import annotations

from typing import Iterable

from model import PIR, PIRRepository, format_datetime
from model.pir import Contact, Event, PlainText, Task


class Formatter:
    """Renders PIRs, PIR lists and error messages as plain text.

    All methods return a string (rather than printing directly) so the
    controller can pass the output to whichever :class:`Reporter` it likes,
    or compose multiple formatted fragments before flushing.
    """

    # Header banner shown when the system starts up
    BANNER = (
        "PIM -- Personal Information Manager\n"
        "Type 'help' to see available commands, 'exit' to quit.\n"
    )

    # Footer shown when the system exits
    FAREWELL = "Bye!  Unsaved changes will be lost; remember to use 'save' next time.\n"

    @staticmethod
    def banner() -> str:
        return Formatter.BANNER

    @staticmethod
    def farewell() -> str:
        return Formatter.FAREWELL

    @staticmethod
    def help_text() -> str:
        lines = [
            "Available commands:",
            "  create <type> <field1>=<value1> <field2>=<value2> ...",
            "        Create a new PIR. <type> is one of plaintext, task, event, contact.",
            "        Each field is given as name=value.  Strings with spaces should be",
            "        quoted with double quotes, e.g.  text=\"hello world\".",
            "        Time fields accept the ISO format YYYY-MM-DDTHH:MM:SS.",
            "  list                              List every PIR (sorted by id).",
            "  show <id>                          Show details of one PIR.",
            "  update <id> <field>=<value>        Update one field of an existing PIR.",
            "  delete <id>                        Delete the given PIR.",
            "  search \"<criterion>\"              Search PIRs matching the criterion.",
            "  save <file.pim>                    Save all PIRs to a .pim file.",
            "  load <file.pim>                    Load PIRs from a .pim file (merges).",
            "  clear                              Remove every PIR from the in-memory repository.",
            "  fields <type>                      List the fields of a PIR type.",
            "  help                               Show this help message.",
            "  exit                               Quit the PIM.",
            "",
            "Criterion DSL examples:",
            '  search "type=task"',
            '  search "type=contact && name~Alice"',
            '  search "deadline<2025-12-31T23:59:59"',
            '  search "type=event && (starting_time>2025-10-01T00:00:00 || alarm>2025-10-01T00:00:00)"',
            '  search "!type=plaintext"',
            "",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_pir(pir: PIR) -> str:
        """Render one PIR as a multi-line block suitable for ``show``.

        The first line is a header with the type and id; subsequent lines
        list each field with its current value.  Time fields are rendered
        in the canonical ISO-ish format so the output is unambiguous and
        easy to copy back into a command.
        """
        cls = pir.__class__
        kind_map = cls.field_kinds()
        lines = [f"{cls.__name__} #{pir.id}"]
        for fname in cls.field_names():
            value = pir.get_field(fname)
            if kind_map.get(fname) == "time":
                rendered = (
                    format_datetime(value) if value is not None else "(none)"
                )
            else:
                rendered = repr(value) if isinstance(value, str) else str(value)
            lines.append(f"  {fname}: {rendered}")
        return "\n".join(lines)

    @staticmethod
    def format_pir_list(pirs: Iterable[PIR]) -> str:
        """Render an iterable of PIRs as a one-line-per-record list suitable
        for ``list`` and ``search`` output."""
        pirs = list(pirs)
        if not pirs:
            return "(no PIRs)"
        lines = []
        for pir in pirs:
            cls = pir.__class__
            # Compact one-liner: type #id, first non-empty field
            primary = Formatter._primary_field_value(pir)
            lines.append(f"  #{pir.id:>3} [{cls.__name__}] {primary}")
        return "\n".join(lines)

    @staticmethod
    def _primary_field_value(pir: PIR) -> str:
        """Return a short, human-readable summary of the most salient field
        of a PIR (the note text, the task description, the contact name,
        the event description)."""
        if isinstance(pir, PlainText):
            return _truncate(pir.get_field("text"))
        if isinstance(pir, Task):
            return _truncate(pir.get_field("description"))
        if isinstance(pir, Event):
            return _truncate(pir.get_field("description"))
        if isinstance(pir, Contact):
            return _truncate(pir.get_field("name"))
        return _truncate(str(pir))

    @staticmethod
    def format_count(n: int) -> str:
        """Render a one-line summary of how many PIRs match a query."""
        if n == 0:
            return "0 PIRs matched."
        if n == 1:
            return "1 PIR matched."
        return f"{n} PIRs matched."

    @staticmethod
    def format_error(message: str) -> str:
        """Render an error message prefixed with a tag so users can tell
        error output apart from normal output at a glance."""
        return f"ERROR: {message}"

    @staticmethod
    def format_info(message: str) -> str:
        """Render an informational message prefixed with a tag."""
        return f"INFO: {message}"

    @staticmethod
    def format_repository_summary(repo: PIRRepository) -> str:
        """Render a short summary of the repository contents (one line per
        PIR type with a count)."""
        counts = {}
        for pir in repo.all():
            counts[pir.__class__.__name__] = counts.get(pir.__class__.__name__, 0) + 1
        if not counts:
            return "Repository is empty."
        lines = [f"  {cls_name}: {n}" for cls_name, n in sorted(counts.items())]
        return f"Repository has {len(repo)} PIR(s):\n" + "\n".join(lines)


def _truncate(s: str, max_len: int = 60) -> str:
    """Truncate a string for one-line display; preserves readability for
    long notes/descriptions while keeping the listing tidy."""
    if s is None:
        return "(empty)"
    s = str(s)
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "..."
