#!/usr/bin/env bash
# Typecheck guard — STEP-001.02
# tsc errors with "No inputs were found" on an empty workspace, which would be a
# false failure. This guard makes the empty case explicit rather than silently
# skipping it, and becomes a real typecheck the moment TypeScript source lands.
set -uo pipefail
cd "$(dirname "$0")/../.."
# BUG-004 (recurrence, found at STEP-002.02): `git ls-files` lists TRACKED files
# only, so files added in the current commit are invisible and the guard reports a
# vacuous pass on its own first run. The BUG-004 fix was applied to some guards but
# not this one. Always union tracked + untracked-not-ignored.
PATTERNS=('apps/**/*.ts' 'apps/**/*.tsx' 'packages/**/*.ts' 'packages/**/*.tsx' 'services/**/*.ts')
files=$( { git ls-files "${PATTERNS[@]}"; git ls-files --others --exclude-standard "${PATTERNS[@]}"; } 2>/dev/null \
        | sort -u | wc -l | tr -d ' ')
if [ "$files" -eq 0 ]; then
  echo "PASS (vacuous): 0 TypeScript files. Real typecheck begins with STEP-002."
  exit 0
fi
echo "Typechecking $files TypeScript file(s)..."
pnpm exec tsc --noEmit -p tsconfig.base.json
