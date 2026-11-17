# PIM System -- Personal Information Manager

A command-line personal information management system written in Python 3.11
using **only the Python standard library**. The system supports four kinds
of personal information records (PIRs):

- **PlainText** -- quick notes
- **Task** -- to-do items with a description and a deadline
- **Event** -- scheduled events with a starting time and an alarm
- **Contact** -- contacts with name, address, and mobile number

PIRs can be created, listed, shown, updated, deleted, and searched by a
flexible boolean criterion DSL. PIRs can be saved to / loaded from a
`.pim` file (JSON inside).

## Quick Start

```bash
cd PIM_System
python3 pim.py
```

This drops you into an interactive REPL. Type `help` for the command
reference, or `exit` (or Ctrl-D) to quit.

## Architecture

The system follows the **Model-View-Controller** pattern:

```
PIM_System/
├── model/                                      # Model layer (no I/O, no UI dependencies)
│   ├── __init__.py                             # Re-exports the public API
│   ├── pir/                                    # PIR base class, registry, and concrete subclasses
│   │   ├── __init__.py                         # Re-exports PIR, subclasses, datetime & registry helpers
│   │   ├── base.py                             # Abstract PIR base class + _PIR_REGISTRY
│   │   ├── datetime_utils.py                   # ISO datetime parsing and formatting
│   │   ├── plaintext.py                        # PlainText PIR subclass
│   │   ├── task.py                             # Task PIR subclass
│   │   ├── event.py                            # Event PIR subclass
│   │   └── contact.py                          # Contact PIR subclass
│   ├── criterion/                              # Search criterion DSL (leaf + composite)
│   │   ├── __init__.py                         # Re-exports Criterion classes and field-index helpers
│   │   ├── base.py                             # Abstract Criterion base class + Criterion.parse()
│   │   ├── field_index.py                      # Dynamic text/time field index across PIR types
│   │   ├── type_criterion.py                   # TypeCriterion (type=...)
│   │   ├── text_criterion.py                   # TextContainsCriterion (field~"...")
│   │   ├── time_criterion.py                   # TimeCompareCriterion (field< / > / =)
│   │   ├── composite.py                        # AndCriterion, OrCriterion, NotCriterion
│   │   ├── tokenizer.py                        # Criterion DSL tokenizer
│   │   └── parser.py                           # Recursive-descent criterion DSL parser
│   ├── exceptions/                             # Custom exception hierarchy
│   │   ├── __init__.py                         # Re-exports all model exceptions
│   │   ├── pim_model_error.py                  # PIMModelError base exception
│   │   ├── unknown_field_error.py              # UnknownFieldError
│   │   ├── invalid_field_value_error.py        # InvalidFieldValueError
│   │   ├── pir_not_found_error.py              # PIRNotFoundError
│   │   ├── duplicate_pir_id_error.py           # DuplicatePIRIdError
│   │   ├── invalid_file_extension_error.py     # InvalidFileExtensionError
│   │   ├── storage_corruption_error.py         # StorageCorruptionError
│   │   ├── unknown_pir_type_error.py           # UnknownPIRTypeError
│   │   └── criterion_syntax_error.py           # CriterionSyntaxError
│   ├── repository.py                           # In-memory store (CRUD + search)
│   └── storage.py                              # .pim file I/O (JSON inside)
├── view/                                       # View layer (output formatting & sinks)
│   ├── __init__.py                             # Re-exports Formatter and Reporter classes
│   ├── formatter.py                            # Formatter (renders PIRs, lists, errors, summaries)
│   └── reporter.py                             # Reporter ABC, PrintReporter, InMemoryReporter
├── controller/                                 # Controller layer (CLI + dispatch)
│   ├── __init__.py
│   ├── parsed_command.py                       # ParsedCommand data structure
│   ├── parser.py                               # CommandTokenizer + TokenizerError
│   ├── commands.py                             # Command dispatcher (12 verbs)
│   └── cli.py                                  # REPL
├── tests/                                      # Unit tests for the model layer
│   ├── __init__.py
│   ├── test_pir.py
│   ├── test_repository.py
│   ├── test_criterion.py
│   ├── test_storage.py
│   └── test_extra.py
├── pim.py                                      # Main entry point
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
model package. See `test_coverage_report.md` for the full breakdown.

## Documentation

The complete documentation for the project lives one directory up (in
`/home/z/my-project/download/`):

- `SRS.docx` -- Software Requirements Specification
- `Design_Document.docx` -- Design document with architecture / class /
  sequence diagrams
- `Developer_Manual.docx` -- How to set up the development environment
- `User_Manual.docx` -- How to use the system
- `Video_Script.docx` -- Storyboard for the implementation demo video
- `Presentation.pdf` -- Slides for the 5-minute presentation
