# Requirements Coverage Report -- PIM System

> Place: root folder of the source code (`PIM_System/requirements_coverage.md`).
> Source: Appendix B user stories US1--US11, and the functional /
> non-functional requirements in the SRS.

## 1. User Story Coverage (Appendix B)

| User Story | Description                                                                          | Implemented? | Covered by Code Module                                                                                                                        | Covered by Tests                                                                                                      |
| ---------- | ------------------------------------------------------------------------------------ | :----------: | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **US1**    | Create different types of PIRs in a single location                                  |    ✅ Yes    | `model/pir/` (4 subclasses: `plaintext.py`, `task.py`, `event.py`, `contact.py`), `controller/commands.py:_cmd_create`, `model/repository.py` | `tests/test_pir.py`, `tests/test_repository.py`                                                                       |
| **US2**    | Create new plain texts as PIRs (quick notes)                                         |    ✅ Yes    | `model/pir/plaintext.py:PlainText`, `controller/commands.py:_cmd_create` (type=plaintext)                                                     | `tests/test_pir.py:TestPlainText`                                                                                     |
| **US3**    | Create new tasks with descriptions and deadlines                                     |    ✅ Yes    | `model/pir/task.py:Task`, `controller/commands.py:_cmd_create` (type=task)                                                                    | `tests/test_pir.py:TestTask`                                                                                          |
| **US4**    | Create new events with descriptions, starting times, alarms                          |    ✅ Yes    | `model/pir/event.py:Event`, `controller/commands.py:_cmd_create` (type=event)                                                                 | `tests/test_pir.py:TestEvent`                                                                                         |
| **US5**    | Create new contacts with names, addresses, mobile numbers                            |    ✅ Yes    | `model/pir/contact.py:Contact`, `controller/commands.py:_cmd_create` (type=contact)                                                           | `tests/test_pir.py:TestContact`                                                                                       |
| **US6**    | Modify data in existing PIRs                                                         |    ✅ Yes    | `model/pir/base.py:PIR.set_field`, `model/repository.py:update`, `controller/commands.py:_cmd_update`                                         | `tests/test_pir.py:TestTask.test_set_deadline_string_is_parsed`, `tests/test_repository.py:test_update_changes_field` |
| **US7**    | Search PIRs by criteria: type, text-contains, time-compare (<, >, =), and (&&), or ( |              | ), negation (!)                                                                                                                               | ✅ Yes                                                                                                                | `model/criterion/` (`type_criterion.py:TypeCriterion`, `text_criterion.py:TextContainsCriterion`, `time_criterion.py:TimeCompareCriterion`, `composite.py:AndCriterion`, `OrCriterion`, `NotCriterion`), `model/criterion/parser.py:_CriterionParser`, `controller/commands.py:_cmd_search` | `tests/test_criterion.py` (DSL parser, leaf matches, composite matches, 22 cases), `tests/test_extra.py` (edge cases) |
| **US8**    | Print detailed info about a specific PIR or all PIRs                                 |    ✅ Yes    | `view/formatter.py:Formatter.format_pir`, `format_pir_list`, `controller/commands.py:_cmd_show`, `_cmd_list`                                  | (exercised end-to-end by CLI smoke test)                                                                              |
| **US9**    | Delete a specified PIR                                                               |    ✅ Yes    | `model/repository.py:remove`, `controller/commands.py:_cmd_delete`                                                                            | `tests/test_repository.py:test_remove_returns_deleted`, `test_remove_missing_id_raises`                               |
| **US10**   | Store PIRs in a `.pim` file                                                          |    ✅ Yes    | `model/storage.py:PIMStorage.save`, `controller/commands.py:_cmd_save`                                                                        | `tests/test_storage.py:TestPIMStorageRoundTrip`, `TestPIMStorageFileFormat`                                           |
| **US11**   | Load PIRs from a `.pim` file                                                         |    ✅ Yes    | `model/storage.py:PIMStorage.load`, `controller/commands.py:_cmd_load`                                                                        | `tests/test_storage.py:TestPIMStorageMerge`, `TestPIMStorageRoundTrip`                                                |

**Summary**: All 11 user stories are fully implemented and covered by automated
tests where appropriate (controller/view layers are exercised end-to-end via
the CLI smoke test rather than unit tests, per the project brief which asks
specifically for unit tests of the _model_).

## 2. Functional Requirements Coverage (from SRS)

| Req ID | Requirement (short)                                        | Implemented? | Implementation Notes                                                                                                    |
| ------ | ---------------------------------------------------------- | :----------: | ----------------------------------------------------------------------------------------------------------------------- | --- | ---------------------------------------------- |
| FR-01  | Create a PlainText PIR with text                           |      ✅      | `PlainText.__init__(text=...)` (`model/pir/plaintext.py`)                                                               |
| FR-02  | Create a Task PIR with description, deadline               |      ✅      | `Task.__init__(description=..., deadline=...)` (`model/pir/task.py`)                                                    |
| FR-03  | Create an Event PIR with description, starting_time, alarm |      ✅      | `Event.__init__(description=..., starting_time=..., alarm=...)` (`model/pir/event.py`)                                  |
| FR-04  | Create a Contact PIR with name, address, mobile            |      ✅      | `Contact.__init__(name=..., address=..., mobile=...)` (`model/pir/contact.py`)                                          |
| FR-05  | Assign a unique id to each PIR on creation                 |      ✅      | `PIR.__init__` (`model/pir/base.py`) with global counter; bumped on load                                                |
| FR-06  | Modify any field of an existing PIR                        |      ✅      | `PIR.set_field` (`model/pir/base.py`), dispatched via `PIRRepository.update`                                            |
| FR-07  | Reject unknown field names with an error                   |      ✅      | `UnknownFieldError` (`model/exceptions/unknown_field_error.py`) raised from `PIR.get_field` / `set_field`               |
| FR-08  | Reject invalid field values with an error                  |      ✅      | `InvalidFieldValueError` (`model/exceptions/invalid_field_value_error.py`) raised from `PIR.set_field` and constructors |
| FR-09  | List all PIRs in id order                                  |      ✅      | `PIRRepository.all()` returns sorted list                                                                               |
| FR-10  | Show one PIR by id                                         |      ✅      | `PIRRepository.get(id)`; `Formatter.format_pir(pir)` (`view/formatter.py`)                                              |
| FR-11  | Delete a PIR by id                                         |      ✅      | `PIRRepository.remove(id)`                                                                                              |
| FR-12  | Search by PIR type                                         |      ✅      | `TypeCriterion` (`model/criterion/type_criterion.py`)                                                                   |
| FR-13  | Search by text-contains on text fields                     |      ✅      | `TextContainsCriterion` (`model/criterion/text_criterion.py`)                                                           |
| FR-14  | Search by time-compare (<, >, =) on time fields            |      ✅      | `TimeCompareCriterion` (`model/criterion/time_criterion.py`) with LT/GT/EQ                                              |
| FR-15  | Combine criteria with AND (&&)                             |      ✅      | `AndCriterion` (`model/criterion/composite.py`)                                                                         |
| FR-16  | Combine criteria with OR (                                 |              | )                                                                                                                       | ✅  | `OrCriterion` (`model/criterion/composite.py`) |
| FR-17  | Negate a criterion with !                                  |      ✅      | `NotCriterion` (`model/criterion/composite.py`)                                                                         |
| FR-18  | Parenthesised grouping of criteria                         |      ✅      | `_CriterionParser._parse_atom` (`model/criterion/parser.py`)                                                            |
| FR-19  | Field name validation at parse time                        |      ✅      | `CriterionSyntaxError` (`model/exceptions/criterion_syntax_error.py`) raised for unknown fields                         |
| FR-20  | Save PIRs to a `.pim` file (JSON)                          |      ✅      | `PIMStorage.save` (atomic write via temp+rename)                                                                        |
| FR-21  | Load PIRs from a `.pim` file (merges)                      |      ✅      | `PIMStorage.load` (no clear-before-load)                                                                                |
| FR-22  | Reject non-`.pim` file extensions                          |      ✅      | `InvalidFileExtensionError` (`model/exceptions/invalid_file_extension_error.py`)                                        |
| FR-23  | Detect corrupt `.pim` files                                |      ✅      | `StorageCorruptionError` (`model/exceptions/storage_corruption_error.py`, 4 corruption paths)                           |
| FR-24  | CLI command parser supports quoted args and key=value      |      ✅      | `controller/parser.py:CommandTokenizer` (`controller/parsed_command.py:ParsedCommand`)                                  |
| FR-25  | REPL with help, exit and EOF handling                      |      ✅      | `controller/cli.py:REPL`                                                                                                |
| FR-26  | Per-PIR-type field listing (for user discoverability)      |      ✅      | `controller/commands.py:_cmd_fields`                                                                                    |
| FR-27  | Clear the in-memory repository                             |      ✅      | `PIRRepository.clear`, `_cmd_clear`                                                                                     |

## 3. Non-Functional Requirements Coverage (from SRS)

| NFR ID | Requirement                                             | Implemented? | Verification                                                                                                           |
| ------ | ------------------------------------------------------- | :----------: | ---------------------------------------------------------------------------------------------------------------------- |
| NFR-01 | Python standard library only -- no third-party packages |      ✅      | Verified by inspecting every `import` statement in the source tree                                                     |
| NFR-02 | Single entry point: `python3 pim.py`                    |      ✅      | `pim.py:main()`                                                                                                        |
| NFR-03 | Python 3.11 target                                      |      ✅      | Uses `from __future__ import annotations`, no 3.12-only syntax                                                         |
| NFR-04 | Cross-platform (no platform-specific paths)             |      ✅      | Uses `os.replace` and `os.path.join` everywhere                                                                        |
| NFR-05 | Model package is isolated                               |      ✅      | `model/__init__.py` exposes the full public API; never imports from `controller` or `view`                             |
| NFR-06 | Reproducible output (id-sorted listing)                 |      ✅      | `PIRRepository.all()` and `.search()` both return id-sorted lists                                                      |
| NFR-07 | Atomic `.pim` writes                                    |      ✅      | `PIMStorage.save` writes to `.tmp` then `os.replace`                                                                   |
| NFR-08 | Forward-compatible PIR type registry                    |      ✅      | Unknown types in a `.pim` file raise `UnknownPIRTypeError` rather than crashing                                        |
| NFR-09 | Robust error handling at controller layer               |      ✅      | Every handler wraps model errors as `ERROR: ...` strings                                                               |
| NFR-10 | Testable (deterministic id counter)                     |      ✅      | `PIR.reset_id_counter(start=1)` (`model/pir/base.py`) for test isolation                                               |
| NFR-11 | All errors derive from `PIMModelError`                  |      ✅      | All 8 custom exceptions under `model/exceptions/` inherit from `PIMModelError` (`model/exceptions/pim_model_error.py`) |
| NFR-12 | The criterion DSL rejects malformed input loudly        |      ✅      | `CriterionSyntaxError` (`model/exceptions/criterion_syntax_error.py`) raised for any malformed expression              |

## 4. What is NOT Implemented

The following items are **intentionally out of scope** per the project
brief, which says _"It is not recommended to add additional features, e.g.,
a GUI or support for online use, to the system."_

| Out-of-scope item           | Reason                                                            |
| --------------------------- | ----------------------------------------------------------------- |
| GUI / web interface         | Project brief explicitly discourages it                           |
| Online sync / cloud storage | Project brief explicitly discourages it                           |
| Multi-user support          | Project brief explicitly discourages it                           |
| Encryption of `.pim` files  | Personal single-user tool, no threat model                        |
| Undo / redo                 | Single-user CLI; user can save before risky ops                   |
| Built-in alarm scheduler    | Out of scope; the system _stores_ alarms, it does not _fire_ them |

## 5. Verification Procedure

To verify all the above claims yourself:

```bash
# 1. Run the unit tests (128 tests, all should pass)
cd PIM_System
python3 -m unittest discover -s tests -v

# 2. Generate the test coverage report (already present in
#    test_coverage_report.md but you can regenerate it)
python3 -m coverage run --branch --source=model -m unittest discover -s tests
python3 -m coverage report

# 3. Run the CLI end-to-end (REPL)
python3 pim.py
# Then type commands like:
#   create task description="Submit report" deadline=2025-12-31T23:59:59
#   list
#   search "type=task && deadline<2026-01-01T00:00:00"
#   save my_data.pim
#   exit
```
