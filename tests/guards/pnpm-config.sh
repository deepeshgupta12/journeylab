#!/usr/bin/env bash
# pnpm configuration sanity — STEP-002.05 (BUG-013)
#
# WHY THIS EXISTS
#   pnpm 11 renamed the install-script allowlist from `onlyBuiltDependencies`
#   (a list, pnpm 10) to `allowBuilds` (a map). Two things made that silent:
#
#   1. `pnpm config get onlyBuiltDependencies` still echoes the old list back, so
#      the setting LOOKS applied while the installer ignores it entirely.
#   2. When pnpm hits a blocked build it AUTO-WRITES a stub into
#      pnpm-workspace.yaml with the literal placeholder "set this to true or
#      false". Committing that stub yields a config that parses, looks
#      deliberate, and does nothing.
#
#   CI caught it only because CI installs from scratch. Locally, an existing
#   node_modules made every command pass.
set -uo pipefail
cd "$(dirname "$0")/../.."
fail=0

# 1. pnpm's auto-written placeholder must never be committed.
if grep -q 'set this to true or false' pnpm-workspace.yaml 2>/dev/null; then
  echo "  FAIL pnpm-workspace.yaml contains pnpm's auto-written placeholder."
  echo "       Replace 'set this to true or false' with an explicit true/false."
  fail=1
else
  echo "  ok   no auto-written placeholder in pnpm-workspace.yaml"
fi

# 2. The dead pnpm 10 keys must not linger and give false assurance.
for dead in onlyBuiltDependencies neverBuiltDependencies; do
  if grep -qE "^${dead}:" pnpm-workspace.yaml 2>/dev/null; then
    echo "  FAIL pnpm-workspace.yaml uses '${dead}' — pnpm 11 ignores it. Use allowBuilds."
    fail=1
  fi
done
grep -qE '^allowBuilds:' pnpm-workspace.yaml 2>/dev/null \
  && echo "  ok   allowBuilds present (pnpm 11 spelling)" \
  || echo "  note no allowBuilds block — fine only while nothing needs a build script"

# 3. package.json's "pnpm" field is no longer read by pnpm 11.
if grep -q '"pnpm"[[:space:]]*:[[:space:]]*{' package.json 2>/dev/null; then
  echo "  FAIL package.json has a \"pnpm\" field — pnpm 11 ignores it silently."
  fail=1
else
  echo "  ok   no dead \"pnpm\" field in package.json"
fi

[ "$fail" -eq 0 ] || { echo "FAIL: pnpm configuration would not do what it appears to."; exit 1; }
echo "PASS: pnpm configuration uses settings this pnpm version actually reads."
