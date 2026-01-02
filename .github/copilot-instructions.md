# Base120 AI Agent Instructions

## Core Concept

Base120 is a **deterministic governance substrate** implementing a frozen validation pipeline:
1. JSON artifact → 2. Schema validation → 3. Subclass → Failure Mode (FM) mapping → 4. FM → Error resolution

This is the **authoritative reference implementation** (v1.0.0). All other language implementations are semantic mirrors that MUST match this repository's outputs byte-for-byte.

## Critical Architecture

### Validation Pipeline (base120/validators/)
The validation chain executes in strict order:
- [schema.py](base120/validators/schema.py): JSON Schema validation using `Draft202012Validator`. Returns `["ERR-SCHEMA-001"]` on any validation failure
- [mappings.py](base120/validators/mappings.py): Maps artifact `class` field to FM codes via [registries/mappings.json](registries/mappings.json)
- [errors.py](base120/validators/errors.py): Resolves FMs to error codes from [registries/err.json](registries/err.json)

**FM30 Dominance Rule**: When FM30 ("Unrecoverable System State") appears in failure modes, it suppresses ALL other errors except those tagged with `"fm": ["FM30"]` in the error registry. See [errors.py#L3-L7](base120/validators/errors.py#L3-L7).

### Golden Corpus Contract
[tests/corpus/](tests/corpus/) defines the authoritative behavior:
- `corpus/valid/*.json` → Must produce empty error list `[]`
- `corpus/invalid/*.json` → Must match byte-for-byte the corresponding `expected/*.errs.json`

This contract is the **executable specification**. Any deviation breaks semantic correctness.

## Registry System

Three immutable JSON registries in [registries/](registries/):
- `mappings.json`: Subclass (e.g., "00", "99") → FM array (e.g., ["FM1", "FM7", "FM30"])
- `fm.json`: FM definitions (FM1-FM30) with human-readable names
- `err.json`: Error registry linking errors to FMs and severities

Registry modification requires governance approval (see [GOVERNANCE.md](GOVERNANCE.md)).

## Key Patterns

### Return Sorted, Deduplicated Error Lists
All validator functions return `sorted(set(errs))`. Example from [validate.py#L23](base120/validators/validate.py#L23).

### Schema-First Validation
Schema errors short-circuit the pipeline. If schema validation fails, return immediately without checking mappings/FMs. See [validate.py#L14-L16](base120/validators/validate.py#L14-L16).

### Deterministic Loading
Tests load registries and schema once at module level (see [test_corpus.py#L8-L16](tests/corpus.py#L8-L16)) to ensure reproducibility.

## Developer Workflows

### Running Tests
```bash
pytest tests/test_corpus.py
```
Both `test_valid_corpus()` and `test_invalid_corpus()` must pass. Invalid corpus tests check exact error list matches.

### Versioning Constraints (v1.0.x)
- v1.0.0 is **frozen** — no semantic changes allowed
- Permitted: Security fixes, CI hardening, documentation
- Prohibited: Schema changes, registry modifications, new failure modes
- See [GOVERNANCE.md](GOVERNANCE.md) for escalation rules

### Adding Corpus Test Cases
1. Create artifact JSON in `tests/corpus/valid/` or `tests/corpus/invalid/`
2. For invalid cases, create expected output in `tests/corpus/expected/<name>.errs.json`
3. Run `pytest` to verify byte-for-byte match

## Common Pitfalls

- **Don't modify registries** without understanding governance freeze policy
- **Don't bypass schema validation** — it's the firewall against malformed input
- **Don't ignore FM30 dominance** — it's an escalation mechanism, not a bug
- **Don't introduce non-determinism** — no timestamps, random IDs, or environment-dependent behavior

## External Dependencies

- `jsonschema>=4.0` (JSON Schema validation)
- `pytest` (test runner, optional dependency)

Built with `setuptools>=61.0` — see [pyproject.toml](pyproject.toml).
