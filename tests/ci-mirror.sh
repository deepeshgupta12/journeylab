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
trap 'rm -rf "$STAGE"' EXIT

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
echo "=== 2. Cold install + verify on Linux ==="
docker run --rm \
  -v "$STAGE":/w \
  -w /w \
  -e CI=true \
  -e PNPM_HOME=/pnpm \
  -e PNPM_STORE_DIR=/pnpm/store \
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
