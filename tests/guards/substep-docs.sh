#!/usr/bin/env bash
# Sub-step documentation guard — BUG-003
#
# BUG-003: STEP-001.04 was committed without IMPL-004, its regression entry or its
# sub-step status update. The log-writing script failed and `git commit` ran in the
# same shell invocation, so it proceeded regardless.
#
# SUB_STEP_PROTOCOL §8 requires documentation in the SAME commit as the work.
# This guard enforces it: every sub-step marked VERIFIED must have a matching
# implementation-log entry, regression-log entry and blast-radius record.
#
# Contract: FAILS (exit 1) if a VERIFIED sub-step is missing any of the three.
set -uo pipefail
cd "$(dirname "$0")/../.."

IMPL="docs/product/10-logs/IMPLEMENTATION_LOG.md"
REG="docs/product/10-logs/REGRESSION_LOG.md"
BRDIR="docs/product/10-logs/blast-radius"

missing=0
checked=0

# BUG-004 (recurrence, found at STEP-002.02): `git ls-files` lists TRACKED files
# only, so files added in the current commit are invisible and the guard reports a
# vacuous pass on its own first run. The BUG-004 fix was applied to some guards but
# not this one. Always union tracked + untracked-not-ignored.
for f in $( { git ls-files 'docs/product/08-steps/sub-steps/**/*.md'; \
               git ls-files --others --exclude-standard 'docs/product/08-steps/sub-steps/**/*.md'; } \
             2>/dev/null | sort -u); do
  grep -q '^status: VERIFIED' "$f" 2>/dev/null || continue
  id=$(grep -m1 '^sub_step_id:' "$f" | awk '{print $2}')
  [ -n "$id" ] || continue
  checked=$((checked + 1))

  # BUG-005: match a real ENTRY HEADING, not a passing mention anywhere in the file.
  # The original greps passed because IMPL-004's prose happened to name STEP-001.03,
  # while IMPL-003 did not exist.
  grep -qE "^## $id — " "$REG" 2>/dev/null || { echo "MISSING regression entry for $id"; missing=$((missing+1)); }
  grep -qE "^## IMPL-[0-9]{3} — $id — " "$IMPL" 2>/dev/null || { echo "MISSING implementation-log entry for $id"; missing=$((missing+1)); }

  br=$(grep -m1 '^blast_radius_id:' "$f" | awk '{print $2}')
  if [ -n "${br:-}" ] && [ "$br" != "BR-NNN" ]; then
    ls "$BRDIR/${br}"-*.md >/dev/null 2>&1 || { echo "MISSING blast-radius record $br for $id"; missing=$((missing+1)); }
  fi
done

if [ "$missing" -gt 0 ]; then
  echo ""
  echo "FAIL: $missing missing record(s) across $checked VERIFIED sub-step(s)."
  echo "SUB_STEP_PROTOCOL §8 requires docs in the same commit as the work."
  exit 1
fi
echo "PASS: all $checked VERIFIED sub-step(s) have implementation, regression and blast-radius records."
exit 0
