# Test Coverage Report -- PIM System Model

## 1. Methodology

Line and branch coverage of the ``model`` package is measured with [coverage.py](https://coverage.readthedocs.io/) (version 7.x or later).  The test suite is run with the ``--branch`` flag so that branch coverage is reported alongside statement coverage.

The coverage scope is deliberately limited to the ``model`` package, in line with the project brief which asks for unit tests of the *system model* (see Deliverable 4 of the project specification).  The ``view`` and ``controller`` packages are exercised end-to-end by the CLI smoke test instead.

## 2. How to Reproduce

From the project root (``PIM_System/``)::

```
python3 -m coverage run --branch --source=model \
    -m unittest discover -s tests
python3 -m coverage report
python3 -m coverage html   # optional: opens an HTML report in a browser
```

## 3. Summary

- Total statements: **679**
- Total branches: **186**
- Statements covered: **641**
- Branches covered: **165**
- **Combined coverage: 93.2%**

## 4. Per-File Coverage

| File | Statements | Branches | Coverage |
|------|-----------:|---------:|---------:|
| `model/__init__.py` | 7/7 | 0/0 (100%) | 100.0% |
| `model/criterion.py` | 285/294 | 83/88 (94%) | 96.3% |
| `model/exceptions.py` | 37/37 | 0/0 (100%) | 100.0% |
| `model/pir.py` | 215/243 | 54/70 (77%) | 85.9% |
| `model/repository.py` | 49/49 | 14/14 (100%) | 100.0% |
| `model/storage.py` | 48/49 | 14/14 (100%) | 98.4% |

## 5. Uncovered Lines

### `model/criterion.py`

Line numbers not exercised by the test suite:

- **83** -- matches() abstract body -- never called on base Criterion.
- **148** -- TokenizerError fallback path for missing closing quote in bareword.
- **158** -- Defensive: tokens that don't match any kind during lookahead.
- **162** -- Same -- defensive branch in tokeniser.
- **187** -- TimeCompareCriterion.__str__ formatting branch (only used in pretty-print).
- **237** -- (no inline note -- see the file's docstrings for context)
- **248** -- (no inline note -- see the file's docstrings for context)
- **482** -- (no inline note -- see the file's docstrings for context)
- **514** -- (no inline note -- see the file's docstrings for context)

### `model/pir.py`

Line numbers not exercised by the test suite:

- **126** -- Abstract field_names() body -- every concrete subclass overrides it.
- **142** -- Abstract get_field() body -- every concrete subclass overrides it.
- **149** -- Abstract set_field() body -- every concrete subclass overrides it.
- **157** -- Abstract to_dict() body -- every concrete subclass overrides it.
- **178** -- Abstract _from_dict() body -- every concrete subclass overrides it.
- **253** -- (no inline note -- see the file's docstrings for context)
- **282** -- (no inline note -- see the file's docstrings for context)
- **291** -- (no inline note -- see the file's docstrings for context)
- **294** -- (no inline note -- see the file's docstrings for context)
- **309** -- (no inline note -- see the file's docstrings for context)
- **310** -- (no inline note -- see the file's docstrings for context)
- **311** -- (no inline note -- see the file's docstrings for context)
- **312** -- (no inline note -- see the file's docstrings for context)
- **316** -- (no inline note -- see the file's docstrings for context)
- **337** -- (no inline note -- see the file's docstrings for context)
- **367** -- (no inline note -- see the file's docstrings for context)
- **377** -- (no inline note -- see the file's docstrings for context)
- **380** -- (no inline note -- see the file's docstrings for context)
- **397** -- (no inline note -- see the file's docstrings for context)
- **398** -- (no inline note -- see the file's docstrings for context)
- **399** -- (no inline note -- see the file's docstrings for context)
- **400** -- (no inline note -- see the file's docstrings for context)
- **402** -- (no inline note -- see the file's docstrings for context)
- **403** -- (no inline note -- see the file's docstrings for context)
- **434** -- (no inline note -- see the file's docstrings for context)
- **487** -- (no inline note -- see the file's docstrings for context)
- **492** -- (no inline note -- see the file's docstrings for context)
- **516** -- (no inline note -- see the file's docstrings for context)

### `model/storage.py`

Line numbers not exercised by the test suite:

- **123** -- Defensive: StorageCorruptionError re-raise branch.

## 6. Test Catalogue

The test suite is organised into five modules under ``tests/``:

| Module | Tests | Coverage focus |
|--------|------:|----------------|
| `test_pir.py`         | ~30 | PIR id allocation, field protocol, validation, (de)serialisation, registry |
| `test_repository.py`  | ~20 | PIRRepository CRUD, bulk access, search dispatch, iteration |
| `test_criterion.py`   | ~35 | Criterion leaf matches, composite matches, DSL parser, error paths |
| `test_storage.py`     | ~20 | .pim round-trip, file format, corruption detection, merge semantics |
| `test_extra.py`       | ~15 | Edge cases, __repr__, error branches, corner cases of the DSL parser |

All tests are auto-runnable with ``python -m unittest discover -s tests``; no manual setup or environment variables are required.
