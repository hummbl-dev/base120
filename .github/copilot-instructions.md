# Base120 AI Agent Instructions (Patched)

## Core Concept

Base120 is a **deterministic governance substrate** implementing a frozen validation pipeline:

1. JSON artifact
2. Schema validation
3. Subclass → Failure Mode (FM) mapping
4. FM → Error resolution

This repository is the **authoritative reference implementation** (v1.0.0).
All other language implementations are **semantic mirrors** and MUST match this repository's outputs **byte-for-byte** under canonical serialization rules defined below.

---

## Critical Architecture

### Validation Pipeline (`base120/validators/`)

The validation chain executes in **strict order**:

1. **Schema validation**

   * `schema.py`: JSON Schema validation using `Draft202012Validator`
   * On any failure, immediately return `["ERR-SCHEMA-001"]`
   * No further validation stages are executed

2. **Subclass → FM mapping**

   * `mappings.py`: Maps artifact `class` field to Failure Modes using `registries/mappings.json`
   * FM arrays are treated as **unordered sets**
   * Duplicate FMs are collapsed

3. **Error resolution**

   * `errors.py`: Resolves FMs to error codes using `registries/err.json`

---

### FM30 Dominance Rule

When FM30 (`"Unrecoverable System State"`) appears in the resolved FM set:

* All other errors are suppressed
* **Only** errors explicitly tagged with `"fm": ["FM30"]` in `err.json` may be emitted

FM30 dominance applies **only during error resolution**, not during schema validation or FM mapping.

---

## Canonical Entry Point

`base120/validators/validate.py::validate()` is the **ONLY supported public entry point**.

* No alternative entry points are permitted
* No side effects outside returned values are allowed

---

## Golden Corpus Contract

`tests/corpus/` defines the **executable specification**:

* `tests/corpus/valid/*.json`
  → MUST return an empty error list `[]`

* `tests/corpus/invalid/*.json`
  → MUST produce error lists that match
  `tests/corpus/expected/*.errs.json` **byte-for-byte**

Any deviation is a semantic failure.

---

## Registry System

Three **immutable** JSON registries in `registries/`:

* `mappings.json`
  Subclass (e.g., `"00"`, `"99"`) → FM array

* `fm.json`
  Failure Mode definitions (`FM1`–`FM30`)

* `err.json`
  Error definitions linked to FMs and severities

Rules:

* Registries are loaded **read-only**
* Registry load failure is a **hard error**
* Registry modification requires explicit governance approval
  (see `GOVERNANCE.md`)

---

## Determinism Rules

### Canonical JSON Serialization

All emitted JSON artifacts MUST:

* Use UTF-8 encoding
* Sort object keys lexicographically
* Emit arrays in declared order
* Use no insignificant whitespace
* Avoid floats unless schema-explicit
* Contain no timestamps, UUIDs, randomness, or environment-dependent data

These rules define the meaning of "byte-for-byte identical."

---

### Error List Semantics

* Errors are deduplicated
* Errors are sorted **lexicographically by error code string**
* Severity, FM number, or registry order MUST NOT affect sorting

All validator functions return:

```python
sorted(set(errs))
```

---

### Schema-First Enforcement

Schema validation is a **hard firewall**.

If schema validation fails:

* Return immediately
* Do NOT attempt FM mapping
* Do NOT attempt error resolution

---

## Developer Workflows

### Running Tests

```bash
pytest tests/test_corpus.py
```

Both tests must pass:

* `test_valid_corpus()`
* `test_invalid_corpus()`

Invalid corpus tests require **exact error list matches**.

---

### Versioning Constraints (v1.0.x)

* v1.0.0 semantics are **frozen**
* Permitted:

  * Security fixes
  * CI hardening
  * Documentation
* Prohibited:

  * Schema changes
  * Registry modifications
  * New failure modes
  * Behavioral changes

See `GOVERNANCE.md` for escalation rules.

---

### Adding Corpus Test Cases

1. Add artifact JSON to:

   * `tests/corpus/valid/` **or**
   * `tests/corpus/invalid/`
2. For invalid cases, add expected output to:

   * `tests/corpus/expected/<name>.errs.json`
3. Run `pytest` and confirm byte-for-byte match

---

## Hard Prohibitions (Non-Negotiable)

Agents and contributors MUST NOT:

* Auto-correct or infer malformed JSON
* Coerce or guess field types
* Introduce warnings or soft failures
* Emit logs to stdout/stderr in library code
* Bypass schema validation
* Modify registries without governance approval
* Introduce non-determinism (time, randomness, environment inspection)
* Perform network or file I/O outside schema + registry loading

Violations break semantic correctness.

---

## External Dependencies

* `jsonschema>=4.0`
* `pytest` (test execution only)

Built with `setuptools>=61.0` — see `pyproject.toml`.

---

**Status**:
This document is now **enforcement-grade**, Copilot-safe, and suitable for canonical freeze.
