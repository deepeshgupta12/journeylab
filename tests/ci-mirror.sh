#!/usr/bin/env bash
# Run CI's job locally, in CI's conditions — STEP-002.05 follow-up.
#
# WHY THIS EXISTS
#   Five CI failures (BUG-006, 008, 012, 013, 014) and four of them shared one
#   root cause: I verified in an environment that could not reproduce CI's.
#
#     BUG-008  CI is Linux; I asserted a macOS Homebrew path
#     BUG-012  I regenerated a file AFTER the verify that blessed it
#     BUG-013  CI installs with no node_modules; my warm install hid a dead
#              config key, and `pnpm config get` echoed it back as if applied
#     BUG-014  CI checks out only tracked files; my working directory had a
#              tool's 9.2 MB SQLite index that `git add -A` swept in
#
#   Every one of those is invisible on a developer machine by construction. No
#   additional guard fixes that, because the guards run in the same broken
#   environment. The gap is the environment.
#
# WHAT THIS DOES
#   Reproduces the three conditions that actually differ:
#     1. LINUX          — runs in node:24-bookworm, not macOS
#     2. CLEAN CHECKOUT — `git archive HEAD` into a temp dir, so anything
#                         untracked or gitignored simply is not there
#     3. COLD INSTALL   — no node_modules, `--frozen-lockfile`, like CI
#
#   Run this before pushing anything that touches dependencies, workspace
#   configuration, generated files, or CI itself.
#
# Usage: bash tests/ci-mirror.sh
set -uo pipefail
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

if ! docker info >/dev/null 2>&1; then
  echo "SKIP: Docker is not running. This is a SKIP, not a PASS — the Linux/clean/cold"
  echo "      conditions were not tested. Start Docker and re-run before pushing."
  exit 2
fi

STAGE="$(mktemp -d)"

# STEP-001.07: CI now runs a PostgreSQL service, so the mirror must too — a
# mirror that omits the thing CI provides stops being a mirror. GitHub Actions
# service containers have no local equivalent, so this uses a container on a
# user-defined network and reaches it by name. **The two mechanisms differ, so
# neither run proves the other**; both are exercised before pushing.
MIRROR_NET="journeylab-mirror-$$"
MIRROR_DB="journeylab-mirror-db-$$"
cleanup() {
  rm -rf "$STAGE"
  docker rm -f "$MIRROR_DB" >/dev/null 2>&1 || true
  docker network rm "$MIRROR_NET" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== 1. Clean checkout of HEAD (tracked files only) ==="
# A real clone, not `git archive`: several guards call `git ls-files`, so the
# staged copy needs .git to exist. A clone contains only COMMITTED content, so
# anything untracked or gitignored is absent — which is the condition that made
# BUG-014 invisible locally.
git clone --quiet --no-hardlinks --local "$REPO_ROOT" "$STAGE/repo" 2>/dev/null
STAGE="$STAGE/repo"
echo "  cloned $(git -C "$STAGE" ls-files | wc -l | tr -d ' ') tracked file(s) at $(git -C "$STAGE" rev-parse --short HEAD)"
if [ -e "$STAGE/node_modules" ]; then
  echo "  FAIL: node_modules present in a clean checkout — it must be gitignored."
  exit 1
fi
echo "  no node_modules (cold install confirmed)"

echo ""
echo "=== 1b. PostgreSQL, as CI provides it ==="
docker network create "$MIRROR_NET" >/dev/null 2>&1 || true
if ! docker run -d --rm --name "$MIRROR_DB" --network "$MIRROR_NET" \
  -e POSTGRES_USER=journeylab \
  -e POSTGRES_PASSWORD=journeylab_dev_only \
  -e POSTGRES_DB=journeylab \
  postgres:18-alpine >/dev/null; then
  echo "  FAIL: could not start the mirror database (docker run failed above)."
  exit 1
fi

# Wait for readiness rather than sleeping. BUG-009 was a first-boot restart being
# mistaken for a missing schema; a fixed sleep either wastes time or reproduces it.
for _ in $(seq 1 60); do
  if docker exec "$MIRROR_DB" pg_isready -U journeylab >/dev/null 2>&1; then break; fi
  sleep 1
done
if ! docker exec "$MIRROR_DB" pg_isready -U journeylab >/dev/null 2>&1; then
  # DIAGNOSE, do not just fail. "Never became ready" with no evidence is the
  # BUG-009 shape exactly — a message that sends the reader hunting the wrong
  # problem. Print what the container actually said.
  echo "  FAIL: the mirror database never became ready after 60s."
  echo "  --- container status ---"
  docker ps -a --filter "name=$MIRROR_DB" --format "    {{.Status}} ({{.Image}})" || true
  echo "  --- last container log lines ---"
  docker logs "$MIRROR_DB" 2>&1 | tail -15 | sed "s/^/    /" || true
  exit 1
fi
echo "  postgres:18-alpine ready on network $MIRROR_NET"

echo ""
echo "=== 2. Cold install + verify on Linux ==="
docker run --rm \
  -v "$STAGE":/w \
  -w /w \
  --network "$MIRROR_NET" \
  -e CI=true \
  -e PNPM_HOME=/pnpm \
  -e PNPM_STORE_DIR=/pnpm/store \
  -e JOURNEYLAB_DATABASE_URL="postgresql://journeylab:journeylab_dev_only@${MIRROR_DB}:5432/journeylab" \
  -e JOURNEYLAB_REQUIRE_DB=1 \
  node:24-bookworm \
  bash -euo pipefail -c '
    # NOTE: this whole block is inside SINGLE quotes, so backslash-escaped double
    # quotes do NOT work here — they stay literal and node gets a syntax error.
    # Read packageManager with sed rather than nesting quotes.
    PM=$(sed -n "s/.*\"packageManager\": *\"\([^\"]*\)\".*/\1/p" package.json)
    test -n "$PM" || { echo "could not read packageManager from package.json"; exit 1; }
    echo "--- installing ${PM} ---"
    npm i -g "${PM}" >/dev/null 2>&1
    echo "--- pnpm install --frozen-lockfile ---"
    # --store-dir keeps the content-addressable store OUT of the workspace, as CI
    # does. Without it the store lands in .pnpm-store inside the repo and trips the
    # artifact guard. NOTE: no apostrophes anywhere in this single-quoted block.
    pnpm install --frozen-lockfile --store-dir /pnpm/store
    echo "--- installing uv ---"
    # node:24-bookworm ships no pip. Use uv official installer (same binary CI gets
    # from astral-sh/setup-uv).
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
    export PATH="$HOME/.local/bin:$PATH"
    echo "--- uv sync --frozen ---"
    uv sync --frozen
    # STEP-003.08: pnpm verify now runs a real browser. CI installs Chromium and
    # its system libraries the same way; without this the mirror would pass a
    # commit that CI rejects, which is the one failure mode it exists to prevent.
    echo "--- playwright install chromium ---"
    # Two container details, neither of which is a repo defect — but the mirror
    # is worthless if it cannot get past them.
    #
    # 1. GitHub runners ship a fresh package index; node:24-bookworm does not,
    #    so --with-deps fails with a wall of "Unable to locate package".
    # 2. The image points apt at http://deb.debian.org. Behind an egress proxy
    #    that allows curl but not apt over plain HTTP, every fetch fails with
    #    "Connection failed" and apt STILL EXITS 0, having quietly kept its empty
    #    index. HTTPS sources work, and are the better default regardless.
    sed -i "s|http://deb.debian.org|https://deb.debian.org|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true
    sed -i "s|http://deb.debian.org|https://deb.debian.org|g" /etc/apt/sources.list 2>/dev/null || true
    apt-get -o Acquire::Retries=3 update -qq >/dev/null
    pnpm --filter @journeylab/web exec playwright install --with-deps chromium >/dev/null
    # psql, for R7. The GitHub runner ships it; node:24-bookworm does not, and
    # without it R7 falls back to looking for a container name that does not
    # exist inside this one and exits 2 as a SKIP.
    echo "--- installing postgresql-client ---"
    apt-get install -y -qq postgresql-client >/dev/null
    echo "--- applying migrations ---"
    for m in db/migrations/*.sql; do
      psql -v ON_ERROR_STOP=1 "$JOURNEYLAB_DATABASE_URL" -q -f "$m" >/dev/null
    done
    echo "--- pnpm verify ---"
    pnpm verify
  '
rc=$?

echo ""
if [ "$rc" -eq 0 ]; then
  echo "PASS: CI's job succeeds on Linux, from a clean checkout, with a cold install."
else
  echo "FAIL: CI would reject this commit (exit $rc). Fix before pushing."
fi
exit "$rc"
