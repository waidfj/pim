# PIM System -- Personal Information Manager

A command-line personal information management system written in Python 3.11
using **only the Python standard library**.  The system supports four kinds
of personal information records (PIRs):

* **PlainText** -- quick notes
* **Task** -- to-do items with a description and a deadline
* **Event** -- scheduled events with a starting time and an alarm
* **Contact** -- contacts with name, address, and mobile number

PIRs can be created, listed, shown, updated, deleted, and searched by a
flexible boolean criterion DSL.  PIRs can be saved to / loaded from a
``.pim`` file (JSON inside).

## Quick Start

```bash
cd PIM_System
python3 pim.py
```

This drops you into an interactive REPL.  Type `help` for the command
reference, or `exit` (or Ctrl-D) to quit.

## Architecture

The system follows the **Model-View-Controller** pattern:

```
PIM_System/
├── model/                  # Model layer (no I/O, no UI dependencies)
│   ├── __init__.py         # Re-exports the public API
│   ├── pir.py              # PIR base class + 4 concrete subclasses
│   ├── repository.py       # In-memory store (CRUD + search)
│   ├── criterion.py        # Search criterion DSL (leaf + composite)
│   ├── storage.py          # .pim file I/O (JSON inside)
│   └── exceptions.py       # Custom exception hierarchy
├── view/                   # View layer (output formatting)
│   ├── __init__.py
│   └── formatter.py        # Formatter + Reporter abstractions
├── controller/             # Controller layer (CLI + dispatch)
│   ├── __init__.py
│   ├── parser.py           # Command tokenizer
│   ├── commands.py         # Command dispatcher (12 verbs)
│   └── cli.py              # REPL
├── tests/                  # Unit tests for the model layer
│   ├── __init__.py
│   ├── test_pir.py
│   ├── test_repository.py
│   ├── test_criterion.py
│   ├── test_storage.py
│   └── test_extra.py
├── pim.py                  # Main entry point
├── requirements_coverage.md
├── test_coverage_report.md
└── README.md
```

## Running the Tests

```bash
cd PIM_System
python3 -m unittest discover -s tests
```

To also generate a coverage report:

```bash
python3 -m coverage run --branch --source=model -m unittest discover -s tests
python3 -m coverage report
```

The current test suite has 128 tests with 93% line+branch coverage on the
model package.  See `test_coverage_report.md` for the full breakdown.

## Documentation

The complete documentation for the project lives one directory up (in
`/home/z/my-project/download/`):

* `SRS.docx` -- Software Requirements Specification
* `Design_Document.docx` -- Design document with architecture / class /
  sequence diagrams
* `Developer_Manual.docx` -- How to set up the development environment
* `User_Manual.docx` -- How to use the system
* `Video_Script.docx` -- Storyboard for the implementation demo video
* `Presentation.pdf` -- Slides for the 5-minute presentation
