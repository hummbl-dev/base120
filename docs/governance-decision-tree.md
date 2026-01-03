# Governance Change Classification Decision Tree

Quick reference for determining your change class and requirements.

## 🌳 Decision Tree

Start here and follow the branches:

```
┌─────────────────────────────────────┐
│  What files are you changing?       │
└──────────────┬──────────────────────┘
               │
               ▼
       ┌───────┴───────┐
       │ Only *.md     │ YES → ┐
       │ files?        │       │
       └───────┬───────┘       │
               │ NO            │
               ▼               │
       ┌───────┴───────┐       │
       │ registries/   │       │
       │ *.json?       │ YES → [FM - Level 5]
       └───────┬───────┘       │
               │ NO            │
               ▼               │
       ┌───────┴───────┐       │
       │ schemas/ or   │       │
       │ schema.py?    │ YES → [Schema - Level 4]
       └───────┬───────┘       │
               │ NO            │
               ▼               │
       ┌───────┴───────┐       │
       │ tests/corpus/ │ YES → [Corpus - Level 3]
       │               │       │
       └───────┬───────┘       │
               │ NO            │
               ▼               │
       ┌───────┴───────┐       │
       │ base120/      │       │
       │ validators/   │ YES → [FM - Level 5]
       │ (not schema)  │       │
       └───────┬───────┘       │
               │ NO            │
               ▼               │
       ┌───────┴───────┐       │
       │ Breaking any  │ YES → [Breaking - Level 5+]
       │ tests?        │       │
       └───────┬───────┘       │
               │ NO            │
               ▼               │
       ┌───────┴───────┐       │
       │ Other files   │       │
       │ (CI, docs,    │ YES → [Editorial - Level 2]
       │ examples)     │       │
       └───────────────┘       │
                               │
               ┌───────────────┘
               ▼
       ┌───────┴───────┐
       │ Only typos/   │
       │ formatting?   │ YES → [Trivial - Level 1]
       └───────┬───────┘
               │ NO
               ▼
       [Editorial - Level 2]
```

---

## 📊 Quick Classification Matrix

| Files Changed | Semantic Impact | Classification | Level |
|---------------|-----------------|----------------|-------|
| Only *.md (typos) | None | Trivial | 1 |
| docs/, README.md | Structure only | Editorial | 2 |
| tests/corpus/valid/ (add) | New test | Corpus | 3 |
| tests/corpus/valid/ (modify) | Test change | Corpus (needs review) | 3 |
| schemas/*.json | Validation rules | Schema | 4 |
| registries/*.json | FM mappings | FM | 5 |
| base120/validators/*.py | Core logic | FM | 5 |
| Any (breaks tests) | API change | Breaking | 5+ |

---

## ✅ Requirements Checklist

Once you've identified your change class, use this checklist:

### Level 1: Trivial
```
□ Only *.md files changed
□ Only typos/formatting/comments
□ No semantic changes
□ CODEOWNER approval only
```

### Level 2: Editorial
```
□ Documentation structure changes
□ Examples added/improved
□ No code changes
□ CODEOWNER approval only
□ Documentation builds (if applicable)
```

### Level 3: Corpus (Additions)
```
□ Added new test in tests/corpus/
□ All existing tests pass
□ New test passes
□ Justification in commit/PR
□ CODEOWNER approval
□ Audit update (commit message OK)
```

### Level 3: Corpus (Modifications)
```
□ Modified existing test in tests/corpus/
□ Clear justification (why was old test wrong?)
□ All tests pass
□ PR description explains impact
□ CODEOWNER + 1 reviewer approval
□ Audit update in GOVERNANCE.md
```

### Level 4: Schema
```
□ Full test suite passes
□ Corpus diff reviewed
□ Backward compatibility analysis provided
□ Audit update in GOVERNANCE.md
□ CODEOWNER + 1 reviewer approval
□ Mathematical soundness justification
□ v1.0.x: PROHIBITED (unless security fix)
```

### Level 5: FM
```
□ Full test suite passes
□ Mathematical soundness proof provided
□ Impact analysis on all corpus cases
□ Audit update in GOVERNANCE.md with rationale
□ CODEOWNER + 2 reviewers approval
□ Formal proof or detailed justification
□ v1.0.x: PROHIBITED (unless security fix)
```

### Level 5+: Breaking
```
□ Full test suite passes with updated expectations
□ Migration guide for users
□ Deprecation warnings (if phased)
□ Audit update in GOVERNANCE.md
□ Version bump justification
□ CODEOWNER + 3 reviewers approval
□ Governance board approval
□ v1.0.x: PROHIBITED (defer to v1.1.0)
```

---

## 🚦 v1.0.x Special Rules

If `pyproject.toml` version starts with `1.0.`:

### ✅ PERMITTED
- Documentation changes (Level 1-2)
- Corpus additions (Level 3)
- Security fixes (with audit)
- CI hardening (with audit)

### ❌ PROHIBITED
- Schema modifications
- Registry modifications
- Semantic validator changes
- Breaking changes
- New failure modes

### 🔓 Override Process
1. Create issue with "governance-override" label
2. Provide detailed justification
3. Tag @hummbl-dev
4. Wait for governance decision
5. Document override in GOVERNANCE.md

---

## 🤔 Edge Cases

### "I changed multiple types of files"

**Classification:** Highest impact level wins

Example:
- Changed README.md (Level 2)
- Changed tests/corpus/ (Level 3)
- **Result:** Level 3 (Corpus)

### "I only added comments to Python code"

**Classification:** Should be Trivial, but classifier may flag as FM

**Action:**
1. Note in PR description: "Comments only, no semantic changes"
2. CODEOWNER will review and confirm
3. CI warnings OK to ignore in this case

### "My change is permitted in v1.0.x but CI blocks it"

**Classification:** Likely a security fix or CI hardening

**Action:**
1. Verify change is truly permitted (check GOVERNANCE.md)
2. Add "v1.0.x exception: [security/ci]" to PR title
3. Provide justification in PR description
4. Add audit entry to GOVERNANCE.md
5. Request CODEOWNER review

### "I'm fixing a bug, is that breaking?"

**Classification:** Depends on test impact

**Decision:**
- Tests still pass → Not breaking (likely Level 3-5)
- Tests fail, behavior changes → Breaking (Level 5+)
- Tests fail, bug was in tests → Corpus (Level 3)

### "I'm adding a new feature in v1.0.x"

**Classification:** Breaking (prohibited in v1.0.x)

**Action:**
1. Create issue with "v1.1.0" milestone
2. Describe feature
3. Wait for v1.1.0 planning
4. Defer implementation

---

## 📞 Quick Help

### Fast Classification
```bash
# Run this in your branch:
git diff --name-only main | sort

# Count files by type:
git diff --name-only main | grep '\.md$' | wc -l  # Docs
git diff --name-only main | grep 'registries/' | wc -l  # Registries
git diff --name-only main | grep 'corpus/' | wc -l  # Corpus

# If 100% docs → Trivial/Editorial
# If any registries → FM
# If any corpus → Corpus
# If any base120/*.py → FM or Schema
```

### Fast Evidence Check
```bash
# Required for Level 3+:
pytest tests/test_corpus.py -v  # Must pass

# Required for Level 4+:
pytest -v  # Full suite must pass

# Check for audit update:
git diff main GOVERNANCE.md  # Should show changes
```

### Fast v1.0.x Check
```bash
# Check version:
grep '^version' pyproject.toml

# Check prohibited files:
git diff --name-only main | grep -E 'schemas/v1.0.0/|registries/'

# If any matches → PROHIBITED in v1.0.x
```

---

## 🎯 Examples by Scenario

### Scenario: "Fix typo in README"
- **Files:** `README.md`
- **Classification:** Trivial (Level 1)
- **Evidence:** None
- **Audit:** No
- **Reviewers:** CODEOWNER only

### Scenario: "Add new valid corpus test"
- **Files:** `tests/corpus/valid/my-test.json`, `tests/corpus/expected/my-test.errs.json`
- **Classification:** Corpus (Level 3)
- **Evidence:** `pytest tests/test_corpus.py -v` passes
- **Audit:** Justification in commit message
- **Reviewers:** CODEOWNER only

### Scenario: "Fix bug in validator logic"
- **Files:** `base120/validators/validate.py`, `tests/test_corpus.py`
- **Classification:** FM (Level 5) or Breaking (Level 5+)
- **Evidence:** Full test suite passes
- **Audit:** Update GOVERNANCE.md
- **Reviewers:** CODEOWNER + 2-3 reviewers
- **v1.0.x:** PROHIBITED (unless security fix)

### Scenario: "Update documentation examples"
- **Files:** `docs/*.md`, `examples/*.json`
- **Classification:** Editorial (Level 2)
- **Evidence:** Documentation builds (if applicable)
- **Audit:** No
- **Reviewers:** CODEOWNER only

---

## 📚 Related Documentation

- **Full Specification:** [GOVERNANCE.md](../GOVERNANCE.md)
- **Migration Guide:** [governance-migration.md](governance-migration.md)
- **Corpus Contract:** [corpus-contract.md](corpus-contract.md)

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-01-03  
**Related:** GOVERNANCE.md v2.0.0  
**Status:** Reference Guide