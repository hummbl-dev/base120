# Governance v2.0.0 Migration Guide

This guide helps contributors adapt to the formalized governance contract introduced in GOVERNANCE.md v2.0.0.

## What Changed?

### Before (v1.0.0)
- Governance was **descriptive** documentation
- Manual enforcement by CODEOWNER
- Unclear change classification
- No automated validation
- Ad-hoc review requirements

### After (v2.0.0)
- Governance is a **proscriptive contract**
- Automated CI enforcement
- 6 well-defined change classes
- Automated invariant checking
- Clear evidence requirements

---

## Quick Reference: Change Classes

| If you're changing... | Change Class | Impact Level | Min Reviewers |
|-----------------------|--------------|--------------|---------------|
| Typos, formatting in docs | Trivial | 1 | 0 |
| Documentation structure | Editorial | 2 | 0 |
| Test corpus (adding) | Corpus | 3 | 0 |
| Test corpus (modifying) | Corpus | 3 | 1 |
| JSON schemas | Schema | 4 | 1 |
| Registries, validator logic | FM | 5 | 2 |
| Breaking changes | Breaking | 5+ | 3 |

---

## How to Submit Changes Under v2.0.0

### Step 1: Identify Your Change Class

Before creating a PR, determine your change class:

```bash
# What files are you changing?
git status

# Match against patterns:
# - *.md only → Trivial or Editorial
# - tests/corpus/ → Corpus
# - schemas/ or base120/validators/schema.py → Schema
# - registries/ or base120/validators/{mappings,errors,validate}.py → FM
# - Breaking any tests → Breaking
```

### Step 2: Gather Required Evidence

Based on your change class:

**Trivial/Editorial:**
- No evidence required
- Just make the change

**Corpus:**
- Run: `pytest tests/test_corpus.py`
- All tests must pass
- Add justification in commit message if modifying existing corpus

**Schema:**
- Run: `pytest` (full suite)
- Document backward compatibility impact
- Update GOVERNANCE.md or CHANGELOG

**FM/Breaking:**
- Run: `pytest` (full suite)
- Provide mathematical soundness justification
- Update GOVERNANCE.md with audit entry
- Create migration guide (if breaking)

### Step 3: Create Pull Request

The new governance workflows will automatically:

1. **Classify your change** → Posts comment with classification
2. **Check invariants** → Runs determinism, compatibility checks
3. **Verify audit** → Checks for required documentation updates
4. **Enforce version policy** → Blocks prohibited v1.0.x changes

### Step 4: Address CI Feedback

If CI fails:

- **Read the error message carefully** → It will tell you exactly what's wrong
- **Missing audit?** → Update GOVERNANCE.md or CHANGELOG
- **Test failure?** → Fix your code or update test expectations
- **Policy violation?** → Check if change is prohibited in v1.0.x

### Step 5: Get Required Approvals

Based on your change class, wait for:
- CODEOWNER approval (always required)
- 0-3 additional reviewers (depends on impact level)

---

## Common Scenarios

### Scenario 1: Fixing a Typo

**What you're doing:** Fixing typo in README.md

**Change class:** Trivial (Level 1)

**Steps:**
```bash
# 1. Fix the typo
vim README.md

# 2. Commit
git add README.md
git commit -m "Fix typo in README.md"

# 3. Push
git push

# 4. Create PR
# CI will classify as "trivial"
# CODEOWNER approval only
# Merge!
```

**Evidence required:** None

**Audit required:** No

---

### Scenario 2: Adding a Corpus Test

**What you're doing:** Adding a new valid corpus test case

**Change class:** Corpus (Level 3)

**Steps:**
```bash
# 1. Create test case
cat > tests/corpus/valid/my-new-test.json << EOF
{
  "id": "test-001",
  "domain": "core",
  "class": "00",
  "instance": "example",
  "models": ["FM1"]
}
EOF

# 2. Create expected output
cat > tests/corpus/expected/my-new-test.errs.json << EOF
[]
EOF

# 3. Run tests
pytest tests/test_corpus.py -v
# Must pass!

# 4. Update GOVERNANCE.md (audit trail)
# Add to "Recent Corpus Additions" section or similar

# 5. Commit with justification
git add tests/corpus/
git commit -m "Add corpus test for FM1 basic case

Rationale: Expand coverage of FM1 failure mode
Impact: No existing tests affected, adds validation for edge case
"

# 6. Create PR
# CI will classify as "corpus"
# CODEOWNER approval required
# All tests must pass
```

**Evidence required:** Test results, justification

**Audit required:** Yes (update GOVERNANCE.md or commit message)

---

### Scenario 3: Modifying Validator Logic (PROHIBITED in v1.0.x)

**What you're doing:** Changing `base120/validators/validate.py`

**Change class:** FM (Level 5)

**v1.0.x Status:** ❌ PROHIBITED

**What to do:**
```bash
# If you're on v1.0.x:
# 1. Check pyproject.toml version
grep version pyproject.toml
# If it says "1.0.x", your change is PROHIBITED

# 2. Options:
#    a) Defer to v1.1.0 (recommended)
#    b) Request governance override (emergency only)

# 3. If deferring to v1.1.0:
#    - Create GitHub issue describing the change
#    - Tag with "v1.1.0" milestone
#    - Wait for v1.1.0 planning

# 4. If requesting override:
#    - Create GitHub issue with "governance-override" label
#    - Provide detailed justification
#    - Tag @hummbl-dev
#    - Wait for governance decision
```

**Evidence required:** N/A (change prohibited)

**Audit required:** Yes (if override granted)

---

### Scenario 4: Security Fix in v1.0.x

**What you're doing:** Fixing a security vulnerability in validator

**Change class:** FM (Level 5) with override

**v1.0.x Status:** ✅ PERMITTED (security fixes allowed)

**Steps:**
```bash
# 1. Make the fix
vim base120/validators/validate.py

# 2. Add tests proving the fix
pytest tests/ -v

# 3. Document in GOVERNANCE.md
# Add to "Security Fixes" section:
# "2026-01-03: Fixed CVE-XXXX in validate.py (see commit abc123)"

# 4. Commit with security justification
git add base120/ tests/
git commit -m "Security: Fix input validation bypass (CVE-XXXX)

Impact: Addresses potential injection vulnerability
Severity: High
Backward Compatibility: Preserved (stricter validation only)
v1.0.x Exception: Security fix (see GOVERNANCE.md v1.0.x policy)
"

# 5. Create PR with "security" label
# CI will warn about FM changes but allow security fixes
# Needs CODEOWNER + 1 reviewer (security review)
```

**Evidence required:** Test results, security justification, audit update

**Audit required:** Yes (GOVERNANCE.md)

---

## Frequently Asked Questions

### Q: The classifier says my change is "fm" but I only changed comments

**A:** The classifier is conservative. Add a comment to your PR explaining that only comments changed. CODEOWNER will review and may override the classification.

### Q: Do I need to update GOVERNANCE.md for every PR?

**A:** Only for Level 3+ changes (Corpus, Schema, FM, Breaking). Trivial and Editorial changes don't require audit updates.

### Q: Can I modify an existing corpus test?

**A:** Yes, but requires:
- Clear justification (why is the existing test wrong?)
- 1+ external reviewer approval
- Audit trail update

### Q: What if CI is wrong and blocks my PR?

**A:** 
1. First, verify CI is actually wrong (read error message carefully)
2. If truly a false positive, comment on PR with justification
3. Tag @hummbl-dev for governance override
4. Document override in PR description

### Q: How do I add a new failure mode?

**A:** In v1.0.x, you cannot. New FMs require v1.1.0+. Create an issue with "v1.1.0" milestone.

### Q: What's the difference between audit in GOVERNANCE.md vs CHANGELOG?

**A:** 
- **GOVERNANCE.md:** For policy changes, security fixes, overrides
- **CHANGELOG:** For version release notes, user-facing changes
- Either satisfies the audit requirement for most changes

### Q: Can I split a large change into multiple PRs?

**A:** Yes! Recommended approach:
1. PR 1: Documentation (Level 2)
2. PR 2: Corpus additions (Level 3)
3. PR 3: Code changes (Level 4-5)

Each PR gets classified and reviewed independently.

---

## Troubleshooting Common CI Failures

### Failure: "Registry modifications detected in v1.0.x"

**Cause:** You modified `registries/*.json` and version is v1.0.x

**Fix:** 
- If unintentional: `git checkout origin/main -- registries/`
- If intentional: Defer to v1.1.0 or request governance override

---

### Failure: "Corpus outputs differ across runs"

**Cause:** Non-determinism in validator (timestamps, randomness, etc.)

**Fix:** 
- Check for `datetime.now()`, `random()`, `uuid4()` in your changes
- Remove non-deterministic code
- Ensure error lists are sorted

---

### Failure: "Test corpus/test_invalid_corpus FAILED"

**Cause:** Your change affected expected error outputs

**Fix:**
- If intentional: Update `tests/corpus/expected/*.errs.json`
- If unintentional: Fix your code to preserve semantics

---

### Failure: "Missing audit update"

**Cause:** Level 3+ change without GOVERNANCE.md or CHANGELOG update

**Fix:**
```bash
# Add audit entry
vim GOVERNANCE.md
# Add to relevant section or create new section

# Commit
git add GOVERNANCE.md
git commit -m "Add audit trail for [change description]"
git push
```

---

## Rollout Timeline

### Phase 1: Soft Enforcement (Current)
- ✅ All workflows active
- ⚠️ Most checks are warnings, not hard failures
- ✅ Education and feedback period
- ⏰ Duration: 2-4 weeks

### Phase 2: Gradual Hardening
- ✅ Audit checks become hard failures
- ✅ Version policy strictly enforced
- ⚠️ Change classifier suggestions become requirements
- ⏰ Duration: 2-4 weeks

### Phase 3: Full Enforcement
- ✅ All checks are hard failures
- ✅ No overrides except security/emergency
- ✅ Governance contract fully automated
- ⏰ Target: After team training complete

---

## Getting Help

**Documentation:**
- Read GOVERNANCE.md (full contract specification)
- Check this migration guide (common scenarios)

**Issues:**
- Create GitHub issue with "governance" label
- Describe your scenario and ask for guidance

**Escalation:**
- Tag @hummbl-dev in PR comments
- Use "governance-override" label for urgent requests

---

## Feedback

This is v2.0.0 of the governance contract. We want your feedback!

**Found an issue?**
- Create issue with "governance" label
- Describe the problem and proposed fix

**Workflow too strict?**
- Comment on issue #19 with your scenario
- Propose adjustment to change classification

**Documentation unclear?**
- Create issue with "documentation" label
- Tell us what's confusing

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-01-03  
**Related:** GOVERNANCE.md v2.0.0  
**Status:** Active (Soft Enforcement Phase)