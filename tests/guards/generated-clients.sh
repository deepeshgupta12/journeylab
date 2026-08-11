#!/usr/bin/env bash
# Guard: generated clients are never hand-edited and never stale — STEP-004.07.
#
# REQ-PLAT-007: "Generated clients never hand-edited."
#
# HOW THIS IS ENFORCED, AND WHY THAT SHAPE
#   Regenerate, then diff. If the tree differs from what the generator produces,
#   the build fails.
#
#   That single check catches BOTH failures the sub-step names, and cannot tell
#   them apart — which is correct, because they have the same consequence:
#
#     a hand edit          the committed client no longer matches the contract
#     a stale client       the committed client no longer matches the contract
#
#   A guard that distinguished them would need to know intent, and would be
#   guessing. The remedy is identical either way: run the generator.
#
# WHY NOT JUST CHECK FOR A "DO NOT EDIT" HEADER
#   Because a header is advice. Somebody editing a generated file to fix an
#   urgent bug will keep the header, and the next regeneration will silently
#   revert their fix — which is worse than either failing or succeeding, because
#   the fix disappears without a trace and the bug returns.
#
# Contract: FAILS (exit 1) if regeneration changes anything.
# Run: bash tests/guards/generated-clients.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

TS_OUT="packages/contracts/src/generated/openapi.ts"
PY_OUT="apps/api/src/generated/models.py"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git repository" >&2
  exit 2
fi

for f in "$TS_OUT" "$PY_OUT"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: $f does not exist. Run: pnpm contracts:generate"
    exit 1
  fi
done

# Snapshot before regenerating so an unrelated dirty tree cannot be blamed on
# the generator, and so this guard leaves the working directory as it found it.
SNAP="$(mktemp -d)"
trap 'rm -rf "$SNAP"' EXIT
mkdir -p "$SNAP/ts" "$SNAP/py"
cp "$TS_OUT" "$SNAP/ts/openapi.ts"
cp "$PY_OUT" "$SNAP/py/models.py"

if ! uv run python tools/gen_clients.py >/tmp/journeylab-gen-clients.log 2>&1; then
  echo "FAIL: the generator itself failed. See /tmp/journeylab-gen-clients.log"
  tail -5 /tmp/journeylab-gen-clients.log
  exit 1
fi

drift=0
for pair in "$TS_OUT:$SNAP/ts/openapi.ts" "$PY_OUT:$SNAP/py/models.py"; do
  live="${pair%%:*}"
  was="${pair##*:}"
  if ! diff -q "$was" "$live" >/dev/null 2>&1; then
    echo "DRIFT: $live"
    diff -u "$was" "$live" | head -20
    drift=$((drift + 1))
  fi
done

if [ "$drift" -gt 0 ]; then
  echo ""
  echo "FAIL: $drift generated file(s) do not match the contract (REQ-PLAT-007)."
  echo ""
  echo "  Either a generated file was hand-edited, or a contract changed without"
  echo "  regenerating. This guard cannot tell which, and does not need to — both"
  echo "  mean the committed client is not what the contract describes."
  echo ""
  echo "  Fix: pnpm contracts:generate, then commit the result."
  echo ""
  echo "  If you were editing a generated file to fix something, that fix belongs"
  echo "  in the CONTRACT or in the generator. A hand edit is reverted by the next"
  echo "  regeneration, silently, and the bug comes back."
  exit 1
fi

echo "PASS: generated clients match the contract (TypeScript + Python)."
exit 0
