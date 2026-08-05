#!/usr/bin/env bash
# Python typecheck guard — STEP-001.02
# mypy exits non-zero with "no .py[i] files" on an empty tree, a false failure.
set -uo pipefail
cd "$(dirname "$0")/../.."
files=$(git ls-files '*.py' | grep -v '^tests/fixtures/' | wc -l | tr -d ' ')
if [ "$files" -eq 0 ]; then
  echo "PASS (vacuous): 0 Python files. Real typecheck begins with STEP-002."
  exit 0
fi
echo "Typechecking $files Python file(s)..."
uv run mypy .
