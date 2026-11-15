"""Tests package -- unit tests for the PIM model layer.

Tests live under this package so they can be discovered by ``python -m
unittest discover``.  Each module covers one model submodule:

* :mod:`tests.test_pir`         -- PIR base class and 4 subclasses
* :mod:`tests.test_repository`  -- PIRRepository CRUD and search dispatch
* :mod:`tests.test_criterion`   -- Criterion DSL parser and matches
* :mod:`tests.test_storage`     -- .pim file round-trip

Every test class includes a docstring explaining the functionality it
exercises, and every assertion has an explanatory message so failures are
self-describing.
"""
