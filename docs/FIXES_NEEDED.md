# Critical Fixes Needed

Based on independent evaluation (see EVALUATION_REPORT.md), here are the issues that should be fixed:

## 🔴 HIGH PRIORITY

### 1. Fix README CLI Syntax Error

**Files to update:** README.md

**Lines 174, 180** currently show:
```bash
agenticom workflow run feature-dev -i "Add login button" --dry-run
agenticom workflow run feature-dev -i "Add a hello world function"
```

**Should be:**
```bash
agenticom workflow run feature-dev "Add login button" --dry-run
agenticom workflow run feature-dev "Add a hello world function"
```

**Reason:** The `-i` flag doesn't exist. Users following README will get error.

**Fix:**
```bash
# Find and replace in README.md
sed -i '' 's/workflow run \([^ ]*\) -i /workflow run \1 /g' README.md
```

---

## 🟡 MEDIUM PRIORITY

### 2. Clarify Development Setup

**File to update:** README.md (Install section)

**Current:** Shows `make install` but dev dependencies (pytest, ruff, mypy) aren't included.

**Recommendation:** Add clear note in README:

```markdown
## 📦 Install

**For users (production):**
```bash
make install              # Installs core dependencies only
```

**For developers:**
```bash
make dev                  # Installs core + dev dependencies (pytest, ruff, mypy, black)
```
```

---

## 🟢 LOW PRIORITY

### 3. Memory API Consistency

**File:** `orchestration/memory.py`

**Issue:** `LocalMemoryStore` has `remember()` and `search()` but no `get_recent()` method.

**Options:**
1. Add `get_recent()` method
2. Remove references to it in any documentation

---

## 🟢 NICE TO HAVE

### 4. Improve Guardrails Regex

**File:** Testing showed API key pattern `sk-[a-zA-Z0-9]{20,}` might not catch all cases.

**Test case that passed but shouldn't:**
```python
pipeline.check('sk-ant-api03-abcdefghijklmnopqrstu')  # Should block but didn't
```

**Recommended pattern:**
```python
r'sk-ant-[a-zA-Z0-9\-_]{20,}'  # Better pattern for Anthropic keys
```

---

## Summary

**Critical:** 1 issue (CLI syntax)
**Medium:** 1 issue (documentation clarity)
**Low/Nice-to-have:** 2 issues (API consistency, regex refinement)

**Estimated fix time:** 15-30 minutes

All core functionality works correctly. These are polish issues that improve user experience.
