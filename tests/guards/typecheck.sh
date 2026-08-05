#!/usr/bin/env bash
# Typecheck guard — STEP-001.02
# tsc errors with "No inputs were found" on an empty workspace, which would be a
# false failure. This guard makes the empty case explicit rather than silently
# skipping it, and becomes a real typecheck the moment TypeScript source lands.
set -uo pipefail
cd "$(dirname "$0")/../.."
files=$(git ls-files 'apps/**/*.ts' 'apps/**/*.tsx' 'packages/**/*.ts' 'packages/**/*.tsx' 'services/**/*.ts' 2>/dev/null | wc -l | tr -d ' ')
if [ "$files" -eq 0 ]; then
  echo "PASS (vacuous): 0 TypeScript files. Real typecheck begins with STEP-002."
  exit 0
fi
echo "Typechecking $files TypeScript file(s)..."
pnpm exec tsc --noEmit -p tsconfig.base.json
