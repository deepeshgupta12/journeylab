#!/usr/bin/env bash
# Guard meta-test suite — STEP-001 closure audit.
#
# WHY THIS EXISTS
#   Every guard in tests/guards/ was meta-tested when written — but those tests were
#   ad-hoc shell commands in an implementation session. They were never committed, so
#   nobody else could reproduce the proof that a guard actually catches what it
#   claims. The guards were in the repository; the evidence they work was not.
#
#   That is the same failure shape as BUG-004 (a guard trusted before its scope was
#   tested) and BUG-001's first fix (a meta-test that passed for the wrong reason).
#
# WHAT THIS DOES
#   Seeds a real violation for each guard and asserts the guard FAILS, then removes
#   the seed and asserts it PASSES. A guard that cannot fail is not a guard.
#
#   Assertions check the EXIT CODE, and where a specific rule is claimed, the rule
#   name in the output — never merely "non-zero".
#
# Run: bash tests/guards/meta/run-all.sh
set -uo pipefail
cd "$(dirname "$0")/../../.."

# PORTABILITY (BUG-008): `sed -i ''` is BSD/macOS syntax and fails on GNU sed
# (Linux/CI). This helper works on both.
# NOTE: the BSD branch must call `sed`, not `sedi`. An earlier edit replaced the
# literal inside this very function, making it recurse until SIGSEGV. Do not
# "normalise" the sed calls in this definition.
sedi() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"          # GNU
  else
    sed -i "" "$@"       # BSD/macOS
  fi
}

pass=0; fail=0
CLEANUP=()
cleanup() { for f in "${CLEANUP[@]:-}"; do rm -rf "$f" 2>/dev/null; done; }
trap cleanup EXIT

# assert_guard <name> <script> <expected_exit> [<expected_substring>]
assert_guard() {
  local name="$1" script="$2" want="$3" needle="${4:-}"
  local out rc
  out=$(bash "$script" 2>&1); rc=$?
  if [ "$rc" -ne "$want" ]; then
    echo "  FAIL $name — expected exit $want, got $rc"; fail=$((fail+1)); return
  fi
  if [ -n "$needle" ] && ! echo "$out" | grep -q "$needle"; then
    echo "  FAIL $name — exit $rc correct but output lacks '$needle'"; fail=$((fail+1)); return
  fi
  echo "  ok   $name"; pass=$((pass+1))
}

echo "=== baseline: every guard passes on a clean tree ==="
# change-impact-record.sh is deliberately EXCLUDED from the baseline loop: it is
# state-dependent by design, inspecting uncommitted work. While this suite itself is
# uncommitted it correctly reports a substantive change with no touched record. That
# is the gate working, not failing — asserting exit 0 here would be asserting the
# wrong thing.
for g in tests/guards/*.sh; do
  case "$(basename "$g")" in change-impact-record.sh) continue ;; esac
  assert_guard "$(basename "$g") clean" "$g" 0
done

echo ""
echo "=== BUG-001: stray authoring markup ==="
printf 'x\n%s/content%s\n' '<' '>' > META_SEED_markup.md; CLEANUP+=(META_SEED_markup.md)
assert_guard "no-stray-markup catches untracked file (BUG-004 scope)" tests/guards/no-stray-markup.sh 1 "STRAY MARKUP"
rm -f META_SEED_markup.md
assert_guard "no-stray-markup clean again" tests/guards/no-stray-markup.sh 0

echo ""
echo "=== BUG-002: tracked build artifacts ==="
# Force-add: a gitignored dist/ is CORRECTLY invisible to the guard — it cannot be
# committed by accident. BUG-002 was about node_modules being TRACKED because
# .gitignore did not cover it, so the seed must simulate a tracked artifact.
mkdir -p dist && echo "x" > dist/meta-seed.js; CLEANUP+=(dist)
git add -f dist/meta-seed.js >/dev/null 2>&1
assert_guard "no-tracked-artifacts catches force-added dist/ (BUG-002 shape)" tests/guards/no-tracked-artifacts.sh 1 "TRACKED ARTIFACTS"
git rm -q --cached dist/meta-seed.js >/dev/null 2>&1; rm -rf dist
assert_guard "no-tracked-artifacts clean again" tests/guards/no-tracked-artifacts.sh 0

echo ""
echo "=== REQ-PLAT-003: CODEOWNERS coverage ==="
mv CODEOWNERS /tmp/META_CODEOWNERS.bak
assert_guard "codeowners-coverage catches missing file" tests/guards/codeowners-coverage.sh 1
mv /tmp/META_CODEOWNERS.bak CODEOWNERS
assert_guard "codeowners-coverage clean again" tests/guards/codeowners-coverage.sh 0

echo ""
echo "=== port isolation (owner constraint: shared Docker host) ==="
cp docker-compose.dev.yml /tmp/META_COMPOSE.bak
sedi 's|127.0.0.1:5701:6379|127.0.0.1:6379:6379|' docker-compose.dev.yml
assert_guard "port-collisions catches out-of-block port" tests/guards/port-collisions.sh 1
cp /tmp/META_COMPOSE.bak docker-compose.dev.yml; rm -f /tmp/META_COMPOSE.bak
assert_guard "port-collisions clean again" tests/guards/port-collisions.sh 0

echo ""
echo "=== ADR-003: module boundaries (rule name asserted, not just exit) ==="
assert_guard "module-boundaries self-meta-test" tests/guards/module-boundaries.sh 0 "no-cross-module-internals"

echo ""
echo "=== README accuracy ==="
cp README.md /tmp/META_README.bak
printf '\n[broken](docs/product/DOES_NOT_EXIST.md)\n' >> README.md
assert_guard "readme-accuracy catches broken link" tests/guards/readme-accuracy.sh 1
cp /tmp/META_README.bak README.md; rm -f /tmp/META_README.bak
assert_guard "readme-accuracy clean again" tests/guards/readme-accuracy.sh 0

echo ""
echo "=== CI workflow references ==="
cp .github/workflows/verify.yml /tmp/META_WF.bak
sedi 's|- run: pnpm verify|- run: pnpm does-not-exist|' .github/workflows/verify.yml
assert_guard "workflow-refs catches bogus script" tests/guards/workflow-refs.sh 1
cp /tmp/META_WF.bak .github/workflows/verify.yml; rm -f /tmp/META_WF.bak
assert_guard "workflow-refs clean again" tests/guards/workflow-refs.sh 0

echo ""
echo "=== BUG-003/005: sub-step documentation coupling ==="
cp docs/product/10-logs/IMPLEMENTATION_LOG.md /tmp/META_IMPL.bak
sedi 's|^## IMPL-006 — STEP-001.06 — |## IMPL-006 — wrong heading format — |' docs/product/10-logs/IMPLEMENTATION_LOG.md
assert_guard "substep-docs rejects a mention without a real entry (BUG-005)" tests/guards/substep-docs.sh 1
cp /tmp/META_IMPL.bak docs/product/10-logs/IMPLEMENTATION_LOG.md; rm -f /tmp/META_IMPL.bak
assert_guard "substep-docs clean again" tests/guards/substep-docs.sh 0

echo ""
echo "=== private key material must never be tracked ==="
printf -- "-----BEGIN PRIVATE KEY-----\nseed\n-----END PRIVATE KEY-----\n" > META_SEED_key.pem
CLEANUP+=(META_SEED_key.pem)
git add -f META_SEED_key.pem >/dev/null 2>&1
assert_guard "no-tracked-artifacts catches tracked key material" tests/guards/no-tracked-artifacts.sh 1 "TRACKED KEY MATERIAL"
git rm -q --cached META_SEED_key.pem >/dev/null 2>&1; rm -f META_SEED_key.pem
assert_guard "no-tracked-artifacts clean after key seed" tests/guards/no-tracked-artifacts.sh 0

echo ""
echo "=== BUG-014: tool artifacts caught by shape and size, not just by name ==="
head -c 700000 /dev/urandom > META_SEED_big.bin; CLEANUP+=(META_SEED_big.bin)
git add -f META_SEED_big.bin >/dev/null 2>&1
assert_guard "no-tracked-artifacts catches an oversized binary" tests/guards/no-tracked-artifacts.sh 1 "OVERSIZED"
git rm -q --cached META_SEED_big.bin >/dev/null 2>&1; rm -f META_SEED_big.bin

: > META_SEED_index.db; CLEANUP+=(META_SEED_index.db)
git add -f META_SEED_index.db >/dev/null 2>&1
assert_guard "no-tracked-artifacts catches a tracked embedded database" tests/guards/no-tracked-artifacts.sh 1 "TRACKED DATABASE"
git rm -q --cached META_SEED_index.db >/dev/null 2>&1; rm -f META_SEED_index.db
assert_guard "no-tracked-artifacts clean after shape/size seeds" tests/guards/no-tracked-artifacts.sh 0

echo ""
echo "=== BUG-013: pnpm settings that look applied but are not ==="
cp pnpm-workspace.yaml /tmp/META_WS.bak
sedi 's|  esbuild: true|  esbuild: set this to true or false|' pnpm-workspace.yaml
assert_guard "pnpm-config catches pnpm's auto-written placeholder" tests/guards/pnpm-config.sh 1
cp /tmp/META_WS.bak pnpm-workspace.yaml; rm -f /tmp/META_WS.bak
assert_guard "pnpm-config clean again" tests/guards/pnpm-config.sh 0

echo ""
echo "════════════════════════════════════════"
echo "  meta-tests passed: $pass"
echo "  meta-tests failed: $fail"
if [ "$fail" -gt 0 ]; then
  echo "  RESULT: FAIL — a guard did not behave as claimed."
  exit 1
fi
echo "  RESULT: PASS — every guard demonstrably catches what it claims."
exit 0
