#!/usr/bin/env bash
# Regression guard for BUG-002 — build artifacts / dependencies tracked in git.
#
# BUG-002: `node_modules/` was committed because .gitignore contained only
# `.gitnexus`. Found by the STEP-001.02 pre-change analysis, not by any test —
# this guard closes that gap.
#
# Contract: FAILS (exit 1) if any tracked path is a dependency or build artifact.
set -uo pipefail
cd "$(dirname "$0")/../.."

FORBIDDEN='^(node_modules|dist|build|\.next|\.venv|coverage|htmlcov)/|(^|/)__pycache__/|\.pyc$|(^|/)\.env$|(^|/)\.DS_Store$'
hits=$(git ls-files | grep -E "$FORBIDDEN" || true)
if [ -n "$hits" ]; then
  echo "TRACKED ARTIFACTS (BUG-002 regression):"
  echo "$hits" | head -20
  echo ""
  echo "FAIL: $(echo "$hits" | wc -l | tr -d ' ') forbidden path(s) tracked in git."
  exit 1
fi
echo "PASS: no dependency or build artifacts tracked ($(git ls-files | wc -l | tr -d ' ') files checked)."
exit 0
