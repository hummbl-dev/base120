# Base120 Governance

## Governance Contract

This document defines the **enforceable governance contract** for the Base120 repository—a deterministic governance substrate implementing formal validation pipelines. This contract is **proscriptive**, not descriptive: it specifies mandatory requirements that MUST be enforced by CI automation.

**Key Principles:**
- **Determinism First**: All changes MUST preserve byte-for-byte reproducibility of golden corpus outputs
- **Mathematical Rigor**: Formal model changes require proof of soundness preservation
- **Automation-Enforced**: Invalid changes are rejected by CI before human review
- **Audit Trail**: All substantive changes require documentation updates
- **Future-Proof**: Designed to scale from solo founder to team without rework

**Authority:** This repository is the authoritative reference implementation for Base120 v1.x. All language mirrors MUST conform to outputs defined by the golden corpus in `tests/corpus/`.

---

## Change Taxonomy

All changes are classified into one of six categories. The CI system automatically detects change class based on modified file paths.

### Change Classes

#### 1. Trivial (Impact Level: 1)
**Definition:** Minor corrections with zero semantic impact

**Examples:**
- Typo fixes in documentation
- Whitespace/formatting corrections
- Comment clarifications
- Markdown formatting improvements

**File Patterns:**
- `*.md` (documentation files)
- Comments in code files (no code changes)

**Required Evidence:**
- None

**Review Requirements:**
- 0 external reviewers
- CODEOWNER approval only

**CI Prerequisites:**
- None (no tests required)

**Rollback:** Simple git revert

---

#### 2. Editorial (Impact Level: 2)
**Definition:** Documentation restructuring or content expansion without semantic changes

**Examples:**
- Reorganizing documentation sections
- Adding usage examples
- Expanding explanations
- Creating new documentation files

**File Patterns:**
- `docs/**/*.md`
- `README.md`
- `examples/**/*` (non-code)

**Required Evidence:**
- Documentation builds successfully (if applicable)

**Review Requirements:**
- 0 external reviewers
- CODEOWNER approval only

**CI Prerequisites:**
- Documentation build check (if build system exists)

**Rollback:** Git revert

---

#### 3. Corpus (Impact Level: 3)
**Definition:** Adding or modifying test cases in the golden corpus

**Examples:**
- Adding new valid test cases
- Adding new invalid test cases with expected errors
- Updating expected error outputs (requires justification)

**File Patterns:**
- `tests/corpus/valid/**/*.json`
- `tests/corpus/invalid/**/*.json`
- `tests/corpus/expected/**/*.errs.json`

**Required Evidence:**
- All existing tests pass
- New tests pass
- Corpus diff clearly shows additions
- Justification in commit message or PR description

**Review Requirements:**
- 0 external reviewers (for additions)
- 1+ external reviewers (for modifications to existing corpus)
- CODEOWNER approval required

**CI Prerequisites:**
- `pytest tests/test_corpus.py` passes
- Golden corpus determinism check passes
- No modifications to existing valid corpus without governance approval

**Rollback:** Git revert + rerun tests

---

#### 4. Schema (Impact Level: 4)
**Definition:** Changes to JSON schemas or validation rules

**Examples:**
- Modifying `schemas/v1.0.0/artifact.schema.json`
- Adding new schema versions
- Changing validation constraints

**File Patterns:**
- `schemas/**/*.json`
- `base120/validators/schema.py`

**Required Evidence:**
- Full test suite passes
- Corpus diff shows impact on validation
- Backward compatibility analysis (if v1.0.x)
- Audit update in GOVERNANCE.md or CHANGELOG

**Review Requirements:**
- 1+ external reviewers
- Mathematical soundness verification
- CODEOWNER approval required

**CI Prerequisites:**
- All tests pass (`pytest`)
- Schema validation self-test
- Corpus determinism preserved
- No breaking changes to v1.0.x corpus

**Rollback:** Git revert + schema migration script (if needed)

**Special Constraints (v1.0.x):**
- Schema changes are **PROHIBITED** in v1.0.x
- Escalate to governance review for v1.1.0+

---

#### 5. Formal Model (FM) (Impact Level: 5)
**Definition:** Changes to core validation logic, registries, or failure mode mappings

**Examples:**
- Modifying `registries/mappings.json`
- Modifying `registries/fm.json`
- Modifying `registries/err.json`
- Changes to `base120/validators/mappings.py`
- Changes to `base120/validators/errors.py`
- Changes to `base120/validators/validate.py`

**File Patterns:**
- `registries/**/*.json`
- `base120/validators/**/*.py` (excluding schema.py)

**Required Evidence:**
- Full test suite passes
- Proof of mathematical soundness preservation
- Impact analysis on all corpus cases
- Audit update with rationale
- Migration guide (if breaking)

**Review Requirements:**
- 2+ external reviewers
- Mathematical correctness verification
- Formal proof or detailed justification
- CODEOWNER approval required

**CI Prerequisites:**
- All tests pass (`pytest`)
- Corpus determinism preserved
- Registry hash validation
- FM lifecycle state validation
- No semantic drift from v1.0.0 specification

**Rollback:** Requires careful migration + validation

**Special Constraints (v1.0.x):**
- Registry modifications are **PROHIBITED** in v1.0.x
- FM changes require governance escalation
- Escalate to FM30+ review process

---

#### 6. Breaking (Impact Level: 5+)
**Definition:** Changes that break backward compatibility or require API migration

**Examples:**
- Removing public APIs
- Changing function signatures
- Modifying output formats
- Breaking corpus compatibility

**File Patterns:**
- Any files that cause corpus test failures
- Public API changes in `base120/**/*.py`

**Required Evidence:**
- Full test suite passes with updated expectations
- Migration guide for users
- Deprecation warnings (if phased migration)
- Audit update with detailed rationale
- Version bump justification

**Review Requirements:**
- 3+ external reviewers
- Governance board approval
- Security audit (if applicable)
- CODEOWNER approval required

**CI Prerequisites:**
- All tests pass with new expectations
- Migration tests pass
- Deprecation warnings verified
- Corpus migration path validated

**Rollback:** Requires versioned rollback + user migration support

**Special Constraints (v1.0.x):**
- Breaking changes are **PROHIBITED** in v1.0.x
- Must be deferred to v1.1.0+ with proper versioning

---

## Invariants & Guarantees

These invariants are **testable contracts** that CI MUST enforce. Violations result in automatic PR rejection.

### Invariant 1: Golden Corpus Determinism

**Statement:** For any given artifact input, the validator MUST produce identical error output across all executions, environments, and implementations.

**Formal Definition:**
```
∀ artifact A, ∀ executions e1, e2:
  validate(A, e1) == validate(A, e2)  [byte-for-byte]
```

**CI Enforcement:**
- Run corpus tests 3 times in CI, compare outputs byte-for-byte
- No timestamps, UUIDs, or randomness permitted in validator code
- Error lists MUST be sorted lexicographically
- JSON output MUST use canonical serialization (sorted keys, UTF-8)

**Test Command:**
```bash
pytest tests/test_corpus.py -v
# Run 3 times, hash outputs, compare hashes
```

---

### Invariant 2: FM Lifecycle States

**Statement:** Failure Mode definitions follow a strict lifecycle with valid state transitions only.

**Lifecycle States:**
1. **Draft** → Work in progress, not in registries
2. **Review** → Under evaluation, not in stable release
3. **Stable** → In released version, backward-compatible
4. **Deprecated** → Marked for removal, still functional
5. **Removed** → No longer in registries (versioned removal only)

**Valid Transitions:**
```
Draft → Review → Stable → Deprecated → Removed
       ↓
     Draft (rejected)
```

**Invalid Transitions:**
- Stable → Draft
- Stable → Removed (must go through Deprecated)
- Deprecated → Review

**CI Enforcement:**
- FM lifecycle metadata in `registries/fm.json` (future enhancement)
- Block transitions that skip required states
- Require governance approval for Deprecated → Removed

**Current State (v1.0.x):**
- All FMs (FM1-FM30) are in **Stable** state
- No lifecycle transitions permitted in v1.0.x

---

### Invariant 3: Backward Compatibility

**Statement:** Changes in v1.0.x MUST NOT break any valid artifact that passed validation in a previous v1.0.x release.

**Formal Definition:**
```
∀ artifact A:
  if validate_v1.0.0(A) == [] then validate_v1.0.x(A) == []
```

**CI Enforcement:**
- All tests in `tests/corpus/valid/` MUST return empty error list
- No modifications to existing valid corpus allowed
- New corpus additions only (never modifications)

**Test Command:**
```bash
pytest tests/test_corpus.py::test_valid_corpus -v
```

---

### Invariant 4: Mathematical Soundness

**Statement:** All FM mappings and error resolutions MUST preserve logical consistency with the Base120 formal model.

**Requirements:**
- FM mappings are deterministic (subclass → FM set)
- Error resolution is deterministic (FM set → error codes)
- FM30 dominance rule is always respected
- No circular dependencies in FM relationships

**CI Enforcement:**
- Schema validation passes
- Mapping uniqueness check
- FM30 dominance test cases in corpus
- No orphaned FMs (all referenced FMs exist in registry)

---

### Invariant 5: Audit Trail

**Statement:** Every substantive change MUST have a corresponding audit entry with rationale and impact analysis.

**Required for:**
- Corpus changes (Level 3+)
- Schema changes (Level 4+)
- FM changes (Level 5+)
- Breaking changes (Level 5+)

**Not required for:**
- Trivial changes (Level 1)
- Editorial changes (Level 2)

**CI Enforcement:**
- Check for updates to GOVERNANCE.md or CHANGELOG
- Verify commit messages contain issue references
- Validate PR description includes impact analysis (for Level 3+)

**Audit Format:**
```
Change: [Description]
Files: [List of modified files]
Impact Level: [1-5]
Rationale: [Why this change is necessary]
Corpus Impact: [Which test cases affected]
Rollback Plan: [How to revert if needed]
```

---

## Evidence Requirements

This matrix defines mandatory evidence artifacts for each change class:

| Change Class | Test Suite | Corpus Diff | Audit Update | External Review | Mathematical Proof | Migration Guide |
|--------------|------------|-------------|--------------|-----------------|-------------------|-----------------|
| Trivial      | ❌ None    | ❌ N/A      | ❌ No        | 0               | ❌ No             | ❌ No           |
| Editorial    | ✅ Docs    | ❌ N/A      | ⚠️ Optional  | 0               | ❌ No             | ❌ No           |
| Corpus       | ✅ Pass    | ✅ Required | ✅ Yes       | 0 (add) / 1+ (modify) | ❌ No       | ❌ No           |
| Schema       | ✅ Full    | ✅ Required | ✅ Yes       | 1+              | ⚠️ Justification  | ⚠️ If breaking  |
| FM           | ✅ Full    | ✅ Required | ✅ Yes       | 2+              | ✅ Yes            | ⚠️ If breaking  |
| Breaking     | ✅ Full    | ✅ Required | ✅ Yes       | 3+              | ✅ Yes            | ✅ Required     |

**Legend:**
- ✅ **Required:** Must be provided or CI fails
- ⚠️ **Conditional:** Required based on specific change characteristics
- ❌ **Not Required:** Not applicable or unnecessary

---

## Review Process

### Review Thresholds

Changes require different levels of scrutiny based on impact:

**Level 1-2 (Trivial/Editorial):**
- CODEOWNER approval only
- Merge after approval
- No CI gate (or docs build only)

**Level 3 (Corpus Additions):**
- CODEOWNER approval
- All tests pass
- Corpus determinism check passes
- Merge after approval

**Level 3 (Corpus Modifications):**
- CODEOWNER + 1 external reviewer
- Justification required
- All tests pass
- Merge after 2 approvals

**Level 4 (Schema):**
- CODEOWNER + 1+ external reviewers
- Full test suite passes
- Backward compatibility analysis
- Mathematical soundness justification
- Merge after 2+ approvals

**Level 5 (FM Changes):**
- CODEOWNER + 2+ external reviewers
- Formal proof or detailed justification
- Full test suite passes
- Impact analysis
- Merge after 3+ approvals
- **v1.0.x:** PROHIBITED without governance escalation

**Level 5+ (Breaking):**
- CODEOWNER + 3+ external reviewers
- Governance board approval
- Migration guide required
- Merge after 4+ approvals
- **v1.0.x:** PROHIBITED, defer to v1.1.0+

### Escalation Paths

**When to Escalate:**
1. FM30+ failure modes detected
2. Registry modification requests in v1.0.x
3. Breaking changes proposed for v1.0.x
4. Conflicting invariants
5. Security vulnerabilities

**Escalation Process:**
1. Create GitHub issue with `governance` label
2. Tag `@hummbl-dev` for review
3. Provide detailed impact analysis
4. Wait for governance decision
5. Implement decision with full audit trail

**Emergency Overrides:**
- Security fixes: Can bypass review requirements with post-merge audit
- Hotfixes: CODEOWNER can merge with immediate escalation
- All overrides require post-merge documentation

---

## CI Enforcement

The governance contract is enforced through GitHub Actions workflows that automatically validate changes.

### Workflow 1: Change Classifier

**Purpose:** Automatically detect change class based on modified files

**File:** `.github/workflows/governance-classifier.yml`

**Logic:**
```yaml
1. Detect modified files in PR
2. Match files against change class patterns
3. Determine highest impact level
4. Set required checks based on change class
5. Post classification comment on PR
```

**Outputs:**
- Change class label (trivial/editorial/corpus/schema/fm/breaking)
- Impact level (1-5)
- Required evidence checklist
- Required reviewer count

---

### Workflow 2: Evidence Validator

**Purpose:** Verify required evidence artifacts exist for change class

**File:** `.github/workflows/governance-evidence.yml`

**Checks:**
- Test results uploaded (if required)
- Corpus diff generated (if required)
- Audit update present (if required)
- Migration guide present (if required)
- Mathematical proof/justification (if required)

**Failure Modes:**
- Missing required evidence → Block merge
- Incomplete audit → Block merge
- Missing tests → Block merge

---

### Workflow 3: Invariant Tester

**Purpose:** Run all invariant checks to ensure contract compliance

**File:** `.github/workflows/governance-invariants.yml`

**Tests:**
1. **Golden Corpus Determinism:**
   - Run corpus tests 3 times
   - Hash outputs, compare for byte-for-byte identity
   - Fail if any difference detected

2. **Backward Compatibility:**
   - Run all valid corpus tests
   - Ensure all return empty error list
   - Fail if any valid artifact now fails

3. **Mathematical Soundness:**
   - Validate FM mappings are well-formed
   - Check for orphaned FMs
   - Verify FM30 dominance in test cases

4. **Registry Integrity:**
   - Validate registry JSON schemas
   - Check registry hashes match expected values
   - Fail on any unauthorized registry changes (v1.0.x)

---

### Workflow 4: Review Gate

**Purpose:** Enforce minimum reviewer requirements based on change class

**File:** `.github/workflows/governance-review.yml`

**Logic:**
```yaml
1. Detect change class from classifier
2. Count approvals from required reviewers
3. Block merge if insufficient approvals
4. Allow merge once threshold met
```

**Special Rules:**
- CODEOWNER approval always required
- External reviewers must not be commit authors
- Reviews older than 7 days require re-approval

---

### Workflow 5: Audit Updater

**Purpose:** Ensure audit trail is maintained for substantive changes

**File:** `.github/workflows/governance-audit.yml`

**Checks:**
- GOVERNANCE.md updated (if Level 3+)
- CHANGELOG updated (if Level 3+)
- Commit messages reference issues
- PR description includes impact analysis

**Failure Modes:**
- Missing audit update → Block merge
- Incomplete impact analysis → Request changes

---

### Workflow 6: Version Policy Enforcer

**Purpose:** Enforce v1.0.x frozen specification

**File:** `.github/workflows/governance-version.yml`

**v1.0.x Prohibited Changes:**
- Schema modifications (block immediately)
- Registry modifications (block immediately)
- Breaking changes (block immediately)
- FM semantic changes (block immediately)

**v1.0.x Permitted Changes:**
- Security fixes (with audit)
- CI hardening (with audit)
- Documentation (no audit required)
- Corpus additions (with audit for Level 3+)

**Version Detection:**
- Parse `pyproject.toml` version field
- If version starts with `1.0.`, apply v1.0.x rules
- Else apply standard rules

---

## Lifecycle States

### Formal Model Components

Each component in the Base120 formal model has a lifecycle state:

**Component Types:**
1. **Failure Modes (FM1-FM30)**
2. **Error Codes (ERR-*)**
3. **Schema Versions (v1.0.0, v1.1.0, ...)**
4. **Registry Mappings**
5. **Corpus Test Cases**

**Lifecycle States:**
- **Draft:** Under development, not in main branch
- **Review:** In PR, under evaluation
- **Stable:** Merged to main, part of release
- **Deprecated:** Marked for removal, still functional
- **Removed:** No longer in codebase (versioned removal only)

**State Metadata (Future Enhancement):**
```json
{
  "id": "FM1",
  "name": "Specification Ambiguity",
  "lifecycle_state": "stable",
  "introduced_in": "v1.0.0",
  "deprecated_in": null,
  "removed_in": null,
  "deprecation_reason": null
}
```

**Current State (v1.0.x):**
- All FMs: Stable
- All Error Codes: Stable
- Schema v1.0.0: Stable (frozen)
- All Registry Mappings: Stable (frozen)

---

### Corpus Test Cases

Corpus test cases also follow lifecycle:

**States:**
- **Draft:** Local only, not committed
- **Review:** In PR
- **Golden:** Merged to main, authoritative
- **Archived:** Moved to archive directory (rare)

**Transitions:**
- Draft → Review (submit PR)
- Review → Golden (merge after approval)
- Review → Draft (rejected, iterate)
- Golden → Archived (only with governance approval)

**Never:**
- Golden → Removed (corpus is append-only)

---

## Violation Handling

### Automated Violations

If CI detects a governance violation:

1. **Immediate Feedback:** PR status check fails with clear error message
2. **Actionable Guidance:** Comment posted explaining exact violation and remediation steps
3. **Block Merge:** PR cannot be merged until violation resolved
4. **Escalation:** Repeated violations trigger review by governance board

**Example Violations:**
- Missing required evidence → "Add test results to evidence/"
- Insufficient reviewers → "Requires 2 additional approvals"
- Registry modification in v1.0.x → "Registry changes prohibited in v1.0.x, escalate to governance"
- Corpus determinism failure → "Corpus outputs differ across runs, check for non-determinism"

---

### Manual Overrides

In exceptional circumstances, governance violations may be overridden:

**Override Authority:**
- Security fixes: CODEOWNER
- Emergency hotfixes: CODEOWNER
- Governance policy changes: Governance board (currently @hummbl-dev)

**Override Process:**
1. Document override reason in PR description
2. Add `governance-override` label
3. Post override justification as comment
4. Merge with override label
5. Create follow-up issue for post-merge audit
6. Document override in GOVERNANCE.md

**Override Audit:**
All overrides MUST be documented in GOVERNANCE.md within 7 days with:
- Override reason
- Who authorized override
- Impact assessment
- Remediation plan (if applicable)

---

### Post-Merge Violations

If a violation is discovered after merge:

1. **Immediate Response:** Create incident issue with `governance-violation` label
2. **Impact Assessment:** Evaluate blast radius and affected artifacts
3. **Remediation Plan:** Define steps to resolve violation
4. **Revert Decision:** Decide whether to revert commit or fix forward
5. **Post-Mortem:** Document root cause and prevention measures

---

## Version Policy

### v1.0.x (Current)

**Status:** Frozen specification

**Permitted Changes:**
- Security fixes (with audit)
- CI hardening (with audit)
- Documentation clarifications (no audit for Level 1-2)
- Corpus additions (with audit for Level 3+)

**Prohibited Changes:**
- Schema modifications
- Registry modifications
- Semantic changes to validators
- Breaking changes
- New failure modes
- API changes

**Rationale:** v1.0.x is the authoritative reference implementation. Semantic freeze ensures all mirror implementations can maintain byte-for-byte output compatibility.

---

### v1.1.0+ (Future)

**Planned Features:**
- Signed artifacts
- Extended FM mappings
- Lifecycle state metadata
- Enhanced observability
- Contract unit validation (already merged)

**Change Process:**
- Breaking changes allowed (with migration guide)
- New FMs allowed (with formal justification)
- Schema evolution allowed (with versioning)
- Registry extensions allowed (with backward compatibility)

**Migration:** v1.0.x → v1.1.0 migration guide required before v1.1.0 release.

---

## Canonical Artifacts

These artifacts are cryptographically sealed and MUST NOT be modified:

| Artifact | Path | SHA-256 | Status | Version |
|----------|------|---------|--------|---------|
| Base120 v1.0.0 Seed | `artifacts/base120.v1.0.0.seed.json` | `74c51092b218dcf7b430569fffb36a23ae42aa07f7f1b900479b1721e585656d` | **Sealed** | v1.0.0 |

**MRCC Binding:** `compliance/base120.v1.0.0.seed.mrcc.json`

**Integrity Enforcement:**
- CI verifies SHA-256 matches on every push to `artifacts/` or `compliance/`
- See `.github/workflows/verify-seed.yml`
- Any mismatch blocks merge immediately

---

## Future Enhancements

**Planned Governance Improvements:**
1. Automated change classifier workflow
2. Evidence validator workflow
3. Invariant tester workflow
4. Review gate enforcement
5. Audit trail automation
6. FM lifecycle state metadata in registries
7. Corpus determinism multi-run validation
8. Registry integrity hash checks

**Timeline:**
- Phase 1 (Immediate): This GOVERNANCE.md formalization
- Phase 2 (Next): Implement classifier and evidence validator workflows
- Phase 3 (Future): Full invariant testing and review gate automation

---

## Contact & Escalation

**Governance Authority:** @hummbl-dev (solo founder, all roles)

**Issue Labels:**
- `governance`: Governance-related discussions
- `governance-violation`: Post-merge violation detected
- `governance-override`: Emergency override requested
- `escalation`: Requires governance board review

**Response Times:**
- Level 1-2 changes: 24 hours
- Level 3-4 changes: 48 hours
- Level 5+ changes: 1 week
- Security issues: Immediate

---

**Document Version:** 2.0.0 (Formalized Contract)  
**Last Updated:** 2026-01-03  
**Status:** Enforcement-Grade, CI-Integrated  
**Changelog:** This is the first formal governance contract version, replacing the descriptive v1.0.0 governance documentation.
