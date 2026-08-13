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
  # gallery-gate.sh boots a production server and takes ~15s; it is exercised in
  # its own section below rather than in the fast baseline loop.
  # generated-clients.sh regenerates both clients from the contract (~20s); it is
  # exercised in its own section below rather than in the fast baseline loop.
  case "$(basename "$g")" in change-impact-record.sh|gallery-gate.sh|generated-clients.sh|contract-compatibility.sh|tenant-isolation-gate.sh) continue ;; esac
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
echo "=== Node runtime must match .nvmrc ==="
cp .nvmrc /tmp/META_NVMRC.bak
echo "22" > .nvmrc
assert_guard "node-version catches a local/CI Node split" tests/guards/node-version.sh 1 "but .nvmrc and CI use"
cp /tmp/META_NVMRC.bak .nvmrc; rm -f /tmp/META_NVMRC.bak
assert_guard "node-version clean again" tests/guards/node-version.sh 0

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
echo "=== REQ-NFR-008: RTL stays a configuration change ==="
# A physical property renders identically in the LTR locale everyone develops in,
# so only a source-level check catches it. Seeded as an untracked file to also
# re-assert the BUG-004 scope rule.
printf '.meta-seed {\n  margin-left: 4px;\n}\n' > META_SEED_physical.css
CLEANUP+=(META_SEED_physical.css)
assert_guard "logical-css catches a physical property" tests/guards/logical-css.sh 1 "PHYSICAL CSS"
printf '.meta-seed {\n  left: 0; /* rtl-exempt: meta-test */\n}\n' > META_SEED_physical.css
assert_guard "logical-css honours a reasoned rtl-exempt" tests/guards/logical-css.sh 0
rm -f META_SEED_physical.css
assert_guard "logical-css clean again" tests/guards/logical-css.sh 0

echo ""
echo "=== STEP-003.08: the gallery must stay gated ==="
# The accessibility harness sets JOURNEYLAB_ENABLE_GALLERY, so it can only prove
# the route works WITH the flag. This proves the production case: without it, the
# route that enumerates every internal component must be a 404.
if [ -d apps/web/.next ]; then
  assert_guard "gallery-gate passes on the current build" tests/guards/gallery-gate.sh 0 "is 404 without its flag"
  cp apps/web/src/app/dev/gallery/gate.ts /tmp/META_GATE.bak
  sedi "s|return env\[GALLERY_FLAG\] === '1';|return true;|" apps/web/src/app/dev/gallery/gate.ts
  (cd apps/web && pnpm build >/dev/null 2>&1)
  assert_guard "gallery-gate catches an always-on gate" tests/guards/gallery-gate.sh 1 "without JOURNEYLAB_ENABLE_GALLERY"
  cp /tmp/META_GATE.bak apps/web/src/app/dev/gallery/gate.ts; rm -f /tmp/META_GATE.bak
  (cd apps/web && pnpm build >/dev/null 2>&1)
  assert_guard "gallery-gate clean again" tests/guards/gallery-gate.sh 0
else
  echo "  skip gallery-gate meta-test — no production build present (run pnpm build)"
fi

echo ""
echo "=== STEP-004.07: generated clients must match the contract ==="
# TWO FAILURE MODES, AND THE GUARD MUST CATCH BOTH.
#   A hand edit means someone changed the client instead of the contract.
#   A stale client means someone changed the contract and did not regenerate.
# Both leave the same evidence — a diff — and the guard deliberately does not try
# to tell them apart, because both mean the committed client is not what the
# contract describes. This section proves each one independently.
GEN_TS=packages/contracts/src/generated/openapi.ts
if [ -f "$GEN_TS" ]; then
  assert_guard "generated-clients passes on a clean tree" tests/guards/generated-clients.sh 0 "match the contract"

  cp "$GEN_TS" /tmp/META_GEN_TS.bak
  printf '\nexport type IWasHandEdited = string;\n' >> "$GEN_TS"
  assert_guard "generated-clients catches a hand-edited client" tests/guards/generated-clients.sh 1 "DRIFT"
  cp /tmp/META_GEN_TS.bak "$GEN_TS"; rm -f /tmp/META_GEN_TS.bak

  # The second seed edits the CONTRACT and does not regenerate — the mistake a
  # contributor actually makes, as opposed to the one they would have to go out of
  # their way to make.
  #
  # Both clients are backed up around this seed, not just the contract. The guard
  # regenerates IN PLACE, so a failing run leaves the drifted client on disk;
  # restoring only the contract would carry the seed into the next assertion.
  GEN_PY=apps/api/src/generated/models.py
  cp contracts/openapi.yaml /tmp/META_GEN_OA.bak
  cp "$GEN_TS" /tmp/META_GEN_TS.bak
  cp "$GEN_PY" /tmp/META_GEN_PY.bak
  sedi 's|        handoff_id: { type: string }|        handoff_id: { type: string }\
        meta_seed_field: { type: string }|' contracts/openapi.yaml
  assert_guard "generated-clients catches a contract change without regeneration" tests/guards/generated-clients.sh 1 "DRIFT"
  cp /tmp/META_GEN_OA.bak contracts/openapi.yaml
  cp /tmp/META_GEN_TS.bak "$GEN_TS"
  cp /tmp/META_GEN_PY.bak "$GEN_PY"
  rm -f /tmp/META_GEN_OA.bak /tmp/META_GEN_TS.bak /tmp/META_GEN_PY.bak

  assert_guard "generated-clients clean again" tests/guards/generated-clients.sh 0
else
  echo "  skip generated-clients meta-test — no generated client present (run pnpm contracts:generate)"
fi

echo ""
echo "=== STEP-004.08: a breaking contract change must fail the build ==="
# THE SPECIFIED DELIVERABLE (§7): "a seeded breaking change is actually caught".
#
# Four seeds, chosen so that passing them all requires the classifier to be
# DIRECTION-AWARE rather than merely alarmed:
#   1. a removed operation                  -> BREAKING regardless of direction
#   2. a removed RESPONSE property          -> BREAKING only because it is a response
#   3. the same removal carried by a major bump -> must PASS
#   4. a deprecated operation with no Sunset    -> BREAKING on metadata alone
#
# Seed 3 is the one that matters. A guard that failed on every diff would pass
# seeds 1, 2 and 4 and look healthy.
if [ -f contracts/baseline/openapi.yaml ]; then
  assert_guard "contract-compatibility passes on an unchanged contract" \
    tests/guards/contract-compatibility.sh 0 "no breaking contract change"

  cp contracts/openapi.yaml /tmp/META_OA.bak

  # 1. remove an operation
  uv run python - <<'PY' >/dev/null 2>&1
import pathlib, yaml
p = pathlib.Path("contracts/openapi.yaml")
d = yaml.safe_load(p.read_text())
del d["paths"]["/trips/{tripId}"]
p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
  assert_guard "contract-compatibility catches a removed operation" \
    tests/guards/contract-compatibility.sh 1 "operation_removed\|BREAKING"
  cp /tmp/META_OA.bak contracts/openapi.yaml

  # 2. remove a property from a response schema
  uv run python - <<'PY' >/dev/null 2>&1
import pathlib, yaml
p = pathlib.Path("contracts/openapi.yaml")
d = yaml.safe_load(p.read_text())
trip = d["components"]["schemas"]["Trip"]["properties"]
trip.pop(next(iter(trip)))
p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
  assert_guard "contract-compatibility catches a removed response property" \
    tests/guards/contract-compatibility.sh 1 "BREAKING"
  cp /tmp/META_OA.bak contracts/openapi.yaml

  # 3. the SAME removal, carried by a major version bump -> must pass
  uv run python - <<'PY' >/dev/null 2>&1
import pathlib, yaml
p = pathlib.Path("contracts/openapi.yaml")
d = yaml.safe_load(p.read_text())
trip = d["components"]["schemas"]["Trip"]["properties"]
trip.pop(next(iter(trip)))
d["info"]["version"] = "1.0.0"
p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
  assert_guard "contract-compatibility ALLOWS a breaking change behind a major bump" \
    tests/guards/contract-compatibility.sh 0 "carried by a major"
  cp /tmp/META_OA.bak contracts/openapi.yaml

  # 4. deprecation without a sunset date
  uv run python - <<'PY' >/dev/null 2>&1
import pathlib, yaml
p = pathlib.Path("contracts/openapi.yaml")
d = yaml.safe_load(p.read_text())
d["paths"]["/trips/{tripId}"]["get"]["deprecated"] = True
p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
  assert_guard "contract-compatibility catches a deprecation with no Sunset" \
    tests/guards/contract-compatibility.sh 1 "Sunset"
  cp /tmp/META_OA.bak contracts/openapi.yaml; rm -f /tmp/META_OA.bak

  # 5. THE BYPASS. Moving the baseline is how you make any compatibility diff come
  # out empty, so the check that catches it needs its own seed — otherwise the gate
  # is a lock on a door standing next to an open window.
  cp contracts/baseline/openapi.yaml /tmp/META_BASE.bak
  uv run python - <<'PY' >/dev/null 2>&1
import pathlib, yaml
p = pathlib.Path("contracts/baseline/openapi.yaml")
d = yaml.safe_load(p.read_text())
trip = d["components"]["schemas"]["Trip"]["properties"]
trip.pop(next(iter(trip)))
p.write_text(yaml.safe_dump(d, sort_keys=False))
PY
  assert_guard "contract-compatibility catches a silently moved baseline" \
    tests/guards/contract-compatibility.sh 1 "BASELINE.md was not updated"
  cp /tmp/META_BASE.bak contracts/baseline/openapi.yaml; rm -f /tmp/META_BASE.bak

  # 6. A version claimed in BASELINE.md that the snapshot does not declare.
  cp contracts/baseline/BASELINE.md /tmp/META_MARKER.bak
  sedi 's|^| Baseline version | `0.1.0` ||| Baseline version | `9.9.9` ||' contracts/baseline/BASELINE.md 2>/dev/null \
    || uv run python -c "
import pathlib
p = pathlib.Path('contracts/baseline/BASELINE.md')
p.write_text(p.read_text().replace('| Baseline version | \`0.1.0\` |', '| Baseline version | \`9.9.9\` |', 1))
" >/dev/null 2>&1
  assert_guard "contract-compatibility catches a version the snapshot does not declare" \
    tests/guards/contract-compatibility.sh 1 "but the snapshot declares"
  cp /tmp/META_MARKER.bak contracts/baseline/BASELINE.md; rm -f /tmp/META_MARKER.bak

  assert_guard "contract-compatibility clean again" \
    tests/guards/contract-compatibility.sh 0 "no breaking contract change"
else
  echo "  skip contract-compatibility meta-test — no baseline (run pnpm contracts:baseline)"
fi

echo ""
echo "=== STEP-001.07: a missing database must FAIL where one is declared ==="
# BUG-023 SURVIVED FOR SIX STEPS BECAUSE A SKIP READ AS A PASS.
# Adding PostgreSQL to CI fixes today; this fixes the regression. If the service
# is ever renamed, moved or broken, these are what turn a silent skip back into a
# red build.
NOWHERE="postgresql://nobody:nothing@127.0.0.1:59999/absent"

assert_guard "tenant-isolation gate passes with the stack up" \
  tests/guards/tenant-isolation-gate.sh 0 "cross-tenant isolation enforced"

# Skip tolerated when nothing declared a database — but it must SAY so.
out=$(JOURNEYLAB_DATABASE_URL="$NOWHERE" bash tests/guards/tenant-isolation-gate.sh 2>&1); rc=$?
if [ "$rc" -eq 0 ] && echo "$out" | grep -q "DID NOT RUN"; then
  echo "  ok   no database + no flag -> tolerated, and says loudly that R7 did not run"; pass=$((pass+1))
else
  echo "  FAIL no database + no flag -> expected exit 0 with a loud notice, got $rc"; fail=$((fail+1))
fi

# The ratchet itself.
# TWO LAYERS CAN FIRE HERE, and the first version of this assertion only knew
# about one. The suite itself refuses when JOURNEYLAB_REQUIRE_DB is set, so the
# wrapper's own branch is reached only if the suite ever stops checking. Both are
# correct; assert the OUTCOME and the reason, not one component's wording.
out=$(JOURNEYLAB_REQUIRE_DB=1 JOURNEYLAB_DATABASE_URL="$NOWHERE" bash tests/guards/tenant-isolation-gate.sh 2>&1); rc=$?
if [ "$rc" -eq 1 ] && echo "$out" | grep -qi "JOURNEYLAB_REQUIRE_DB\|declared a database"; then
  echo "  ok   no database + JOURNEYLAB_REQUIRE_DB -> FAILS (the BUG-023 ratchet)"; pass=$((pass+1))
else
  echo "  FAIL expected exit 1 naming the flag; got exit $rc"; fail=$((fail+1))
fi

# And the wrapper's own branch, reached by removing the suite's check. Belt and
# braces are only worth having if each is known to hold on its own.
cp tests/security/test_tenant_isolation.sh /tmp/META_R7.bak
sedi 's|if \[ "${JOURNEYLAB_REQUIRE_DB:-}" != "" \] && \[ "${JOURNEYLAB_REQUIRE_DB:-}" != "0" \]; then|if false; then|' tests/security/test_tenant_isolation.sh
out=$(JOURNEYLAB_REQUIRE_DB=1 JOURNEYLAB_DATABASE_URL="$NOWHERE" bash tests/guards/tenant-isolation-gate.sh 2>&1); rc=$?
if [ "$rc" -eq 1 ] && echo "$out" | grep -q "declared a database"; then
  echo "  ok   the wrapper ratchet holds even if the suite stops checking"; pass=$((pass+1))
else
  echo "  FAIL wrapper ratchet did not fire; exit $rc"; fail=$((fail+1))
fi
cp /tmp/META_R7.bak tests/security/test_tenant_isolation.sh; rm -f /tmp/META_R7.bak

# The same ratchet on the pytest side, which is where the other 41 tests live.
out=$(JOURNEYLAB_REQUIRE_DB=1 JOURNEYLAB_DATABASE_URL="$NOWHERE" \
      uv run pytest tests/api/test_sessions.py -p no:warnings -q 2>&1); rc=$?
if [ "$rc" -ne 0 ] && echo "$out" | grep -q "JOURNEYLAB_REQUIRE_DB is set"; then
  echo "  ok   pytest refuses to skip when a database was declared"; pass=$((pass+1))
else
  echo "  FAIL pytest did not refuse; exit $rc"; fail=$((fail+1))
fi

# And the everyday case still skips rather than failing a laptop with no stack.
out=$(JOURNEYLAB_DATABASE_URL="$NOWHERE" \
      uv run pytest tests/api/test_sessions.py -p no:warnings -q 2>&1); rc=$?
if [ "$rc" -eq 0 ] && echo "$out" | grep -qE "skipped|s "; then
  echo "  ok   pytest still skips on a machine with no stack"; pass=$((pass+1))
else
  echo "  FAIL pytest should skip without the flag; exit $rc"; fail=$((fail+1))
fi

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
