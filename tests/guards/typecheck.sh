#!/usr/bin/env bash
# Typecheck guard — STEP-001.02, rewritten at STEP-002.05
#
# ORIGINAL SHAPE (and why it was wrong)
#   It ran `tsc --noEmit -p tsconfig.base.json` — one root config over every file.
#   That was harmless while there were no TypeScript files, but the moment a real
#   package arrived it typechecked `apps/web` with the ROOT's module settings
#   instead of the package's own, producing a wall of TS1295/TS2835 errors that
#   describe a configuration mismatch rather than a defect in the code.
#
#   A guard that fails for the wrong reason is as bad as one that passes for the
#   wrong reason: both stop telling you about your code.
#
# CURRENT SHAPE
#   Each workspace package typechecks itself with its own tsconfig, via its own
#   `typecheck` script. To stop that becoming a new way to skip checking, this
#   guard FAILS if a package contains TypeScript but declares no typecheck script.
set -uo pipefail
cd "$(dirname "$0")/../.."

# BUG-004 (recurrence, found at STEP-002.02): `git ls-files` lists TRACKED files
# only, so files added in the current commit are invisible and the guard reports a
# vacuous pass on its own first run. Always union tracked + untracked-not-ignored.
PATTERNS=('apps/**/*.ts' 'apps/**/*.tsx' 'packages/**/*.ts' 'packages/**/*.tsx' 'services/**/*.ts')
ts_files=$( { git ls-files "${PATTERNS[@]}"; git ls-files --others --exclude-standard "${PATTERNS[@]}"; } 2>/dev/null | sort -u )
count=$(printf '%s\n' "$ts_files" | grep -c . || true)

if [ "$count" -eq 0 ]; then
  echo "PASS (vacuous): 0 TypeScript files. Real typecheck begins when TypeScript source lands."
  exit 0
fi

echo "Typechecking $count TypeScript file(s) via per-package configs..."

# Every package that owns TypeScript must declare a typecheck script.
missing=0
for pkg in $(printf '%s\n' "$ts_files" | cut -d/ -f1,2 | sort -u); do
  [ -f "$pkg/package.json" ] || { echo "  FAIL $pkg has TypeScript but no package.json"; missing=1; continue; }
  if ! grep -q '"typecheck"' "$pkg/package.json"; then
    echo "  FAIL $pkg has TypeScript but declares no 'typecheck' script — it would go unchecked"
    missing=1
  else
    echo "  ok   $pkg declares a typecheck script"
  fi
done
[ "$missing" -eq 0 ] || { echo "FAIL: a package with TypeScript is not typechecked."; exit 1; }

pnpm -r --if-present typecheck || { echo "FAIL: typecheck errors above."; exit 1; }
echo "PASS: all TypeScript packages typecheck against their own configs."
