#!/usr/bin/env bash
# Python typecheck guard — STEP-001.02
# mypy exits non-zero with "no .py[i] files" on an empty tree, a false failure.
set -uo pipefail
cd "$(dirname "$0")/../.."
# BUG-004 (recurrence, found at STEP-002.02): `git ls-files` lists TRACKED files
# only, so files added in the current commit are invisible and the guard reports a
# vacuous pass on its own first run. The BUG-004 fix was applied to some guards but
# not this one. Always union tracked + untracked-not-ignored.
files=$( { git ls-files '*.py'; git ls-files --others --exclude-standard '*.py'; } \
        | sort -u | grep -v '^tests/fixtures/' | grep -v '^\.venv/' | wc -l | tr -d ' ')
if [ "$files" -eq 0 ]; then
  echo "PASS (vacuous): 0 Python files. Real typecheck begins with STEP-002."
  exit 0
fi
echo "Typechecking $files Python file(s)..."
uv run mypy .
