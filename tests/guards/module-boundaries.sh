#!/usr/bin/env bash
# Module boundary enforcement + meta-test — STEP-001.02
#
# Enforces ADR-003. Two responsibilities:
#   1. Run dependency-cruiser over real source (currently none — passes vacuously).
#   2. META-TEST: build a temporary package pair containing a DELIBERATE boundary
#      violation and assert the rule actually fires.
#
# Requirement (2) exists because a rule that has never been shown to fail is not
# a rule. BUG-001 was initially "verified" by a guard that exited non-zero for the
# wrong reason; this script asserts the specific rule name, not merely failure.
#
# Run: bash tests/guards/module-boundaries.sh
set -uo pipefail

cd "$(dirname "$0")/../.."

FIXTURE_A="packages/zz-boundary-fixture-a"
FIXTURE_B="packages/zz-boundary-fixture-b"

cleanup() { rm -rf "$FIXTURE_A" "$FIXTURE_B"; }
trap cleanup EXIT

echo "=== 1. Boundary check over real source ==="
real_targets=""
for d in apps packages services; do
  [ -d "$d" ] && real_targets="$real_targets $d"
done
if [ -z "$(git ls-files 'apps/**/*.ts' 'packages/**/*.ts' 'services/**/*.ts' 2>/dev/null)" ]; then
  echo "PASS (vacuous): no TypeScript source exists yet — rule applies from STEP-002 onward."
else
  pnpm exec depcruise --config .dependency-cruiser.cjs $real_targets || {
    echo "FAIL: boundary violation in real source"
    exit 1
  }
  echo "PASS: real source respects module boundaries."
fi

echo ""
echo "=== 2. META-TEST: rule must fire on a deliberate violation ==="
mkdir -p "$FIXTURE_A/src" "$FIXTURE_B/src"

cat > "$FIXTURE_A/package.json" <<'JSON'
{ "name": "@journeylab/zz-boundary-fixture-a", "version": "0.0.0", "private": true, "main": "src/index.ts" }
JSON
cat > "$FIXTURE_A/src/internal.ts" <<'TS'
export const privateHelper = (): string => 'internal detail, not public API';
TS
cat > "$FIXTURE_A/src/index.ts" <<'TS'
export { privateHelper } from './internal.js';
TS

cat > "$FIXTURE_B/package.json" <<'JSON'
{ "name": "@journeylab/zz-boundary-fixture-b", "version": "0.0.0", "private": true, "main": "src/index.ts" }
JSON
# DELIBERATE VIOLATION: reaches into package A's internals instead of its entry point
cat > "$FIXTURE_B/src/index.ts" <<'TS'
import { privateHelper } from '../../zz-boundary-fixture-a/src/internal.js';
export const useIt = (): string => privateHelper();
TS

output=$(pnpm exec depcruise --config .dependency-cruiser.cjs "$FIXTURE_B" 2>&1)
rc=$?

if echo "$output" | grep -q 'no-cross-module-internals'; then
  echo "PASS: rule 'no-cross-module-internals' fired on the seeded violation (exit $rc)."
  cleanup
  exit 0
fi

echo "FAIL: seeded boundary violation was NOT caught."
echo "  exit code: $rc"
echo "  expected rule name 'no-cross-module-internals' in output"
echo "--- depcruise output ---"
echo "$output" | head -30
cleanup
exit 1
