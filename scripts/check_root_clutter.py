#!/usr/bin/env python3
"""
Pre-commit hook: reject misplaced files at the repo root.

Rules enforced:
  *.md at root      → must go in docs/   (README.md and CLAUDE.md are exempt)
  test_*.py at root → must go in tests/

Usage (called by pre-commit with staged filenames as argv):
  python scripts/check_root_clutter.py [file ...]
"""

import sys
from pathlib import Path

EXEMPT_MD = {"README.md", "CLAUDE.md"}

violations = []

for arg in sys.argv[1:]:
    path = Path(arg)
    # Only flag files directly at the repo root (no parent directory)
    if path.parent != Path("."):
        continue

    name = path.name

    if name.endswith(".md") and name not in EXEMPT_MD:
        violations.append((arg, "docs/"))
    elif name.startswith("test_") and name.endswith(".py"):
        violations.append((arg, "tests/"))

if violations:
    print("❌  Files must not live at the repo root — move them before committing:\n")
    for filepath, dest in violations:
        print(f"    {filepath}  →  {dest}")
    print(
        "\n    .md files (except README.md / CLAUDE.md) belong in docs/\n"
        "    test_*.py files belong in tests/"
    )
    sys.exit(1)
