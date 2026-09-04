#!/usr/bin/env bash
# README accuracy guard — STEP-001.05
#
# The README is the first thing a new engineer runs. If it drifts from reality it
# wastes their first hour and teaches them the docs cannot be trusted.
#
# This guard proves the README is CURRENT AND CORRECT:
#   1. every `pnpm <script>` it mentions exists in package.json
#   2. every repo-relative path it links to exists
#   3. every port it documents matches docker-compose.dev.yml
#   4. the documented Node PATH actually yields Node 24
#
# It deliberately does NOT run `pnpm verify` — that would recurse, since this
# guard is itself part of `pnpm verify`.
#
# WHAT THIS DOES NOT PROVE: that the README is comprehensible to someone who did
# not write it. That half of the acceptance criterion needs a second human and is
# recorded as outstanding in STEP-001.05 and BR-005 — not claimed as satisfied.
set -uo pipefail
cd "$(dirname "$0")/../.."

README="README.md"
COMPOSE="docker-compose.dev.yml"
fail=0

[ -f "$README" ] || { echo "FAIL: README.md missing"; exit 1; }

echo "1. pnpm scripts referenced in README exist"
# Digits are part of a script name: `a11y` matched as `a` under the old
# `[a-z][a-z:]*` pattern and was reported missing, which is a false failure and
# the kind that gets a guard disabled rather than fixed. `--filter` invocations
# are skipped: the script they name belongs to a workspace package, not the root.
for s in $(grep -oE 'pnpm [a-z][a-z0-9:-]*' "$README" | awk '{print $2}' | sort -u); do
  case "$s" in install|dlx|exec|add|remove|run|why) continue ;; esac
  if node -e "process.exit(require('./package.json').scripts['$s']?0:1)" 2>/dev/null; then
    printf "   ok   pnpm %s\n" "$s"
  else
    printf "   FAIL pnpm %s — not in package.json\n" "$s"; fail=$((fail+1))
  fi
done

echo "2. repo-relative links resolve"
for l in $(grep -oE '\]\([^)#h][^)]*\)' "$README" | sed 's/^](//; s/)$//; s/#.*$//' | sort -u); do
  if [ -e "$l" ]; then printf "   ok   %s\n" "$l"
  else printf "   FAIL %s — does not exist\n" "$l"; fail=$((fail+1)); fi
done

echo "3. documented ports match $COMPOSE"
if [ -f "$COMPOSE" ]; then
  # ONLY THE COMPOSE TABLE, delimited by markers in the README.
  #
  # This used to scan every `| 570X |` row anywhere in the file, which was fine
  # while the only such table listed containers. STEP-007.02 added a second table
  # for APPLICATION ports — Playwright, the Next dev server, the API — none of
  # which compose publishes, and all of which the old scan reported as missing.
  #
  # The markers make the guard's subject explicit rather than inferred from a
  # number, so a third table cannot break it by looking similar.
  compose_table=$(awk '/<!-- compose-ports:start -->/,/<!-- compose-ports:end -->/' "$README")
  if [ -z "$compose_table" ]; then
    printf "   FAIL README has no <!-- compose-ports --> markers to scan\n"; fail=$((fail+1))
  fi
  for p in $(printf '%s\n' "$compose_table" | grep -oE '^\| 5[0-9]{3} ' | tr -d '| '); do
    if grep -q "127.0.0.1:${p}:" "$COMPOSE"; then printf "   ok   %s\n" "$p"
    else printf "   FAIL %s documented as a container port but not published in compose\n" "$p"; fail=$((fail+1)); fi
  done
  for p in $(grep -oE '127\.0\.0\.1:[0-9]+:' "$COMPOSE" | grep -oE ':[0-9]+:' | tr -d ':' | sort -u); do
    if printf '%s\n' "$compose_table" | grep -qE "^\| $p \|"; then :
    else printf "   FAIL %s published in compose but undocumented in README\n" "$p"; fail=$((fail+1)); fi
  done
else
  printf "   FAIL %s missing\n" "$COMPOSE"; fail=$((fail+1))
fi

echo "4. documented Node version is consistent and reachable"
# PORTABILITY (BUG-008): this previously asserted a macOS Homebrew path was
# executable, which can never be true on ubuntu-latest. CI failed for a reason that
# had nothing to do with the README being wrong.
#
# Split into a portable invariant and a host-conditional check:
#   4a. ALWAYS  — the Node major version documented in the README must match .nvmrc,
#                 which is the single source of truth CI's setup-node reads. This is
#                 the check that actually catches README drift.
#   4b. IF PRESENT — where the documented Homebrew path exists (developer macOS),
#                 confirm it really yields that version.
NVMRC_MAJOR=$(tr -d 'v \n' < .nvmrc 2>/dev/null | cut -d. -f1)
README_MAJOR=$(grep -oE 'node@[0-9]+' "$README" | head -1 | grep -oE '[0-9]+')
if [ -z "$README_MAJOR" ]; then
  README_MAJOR=$(grep -oE 'Node(\.js)? \*\*?([0-9]+)' "$README" | grep -oE '[0-9]+' | head -1)
fi

if [ -n "$NVMRC_MAJOR" ] && [ "$README_MAJOR" = "$NVMRC_MAJOR" ]; then
  printf "   ok   README documents Node %s, matching .nvmrc\n" "$README_MAJOR"
else
  printf "   FAIL README documents Node '%s' but .nvmrc says '%s'\n" "${README_MAJOR:-<none>}" "${NVMRC_MAJOR:-<none>}"
  fail=$((fail+1))
fi

NODE_PATH_LINE=$(grep -oE '/opt/homebrew/opt/node@[0-9]+/bin' "$README" | head -1)
if [ -n "$NODE_PATH_LINE" ] && [ -x "${NODE_PATH_LINE}/node" ]; then
  v=$("${NODE_PATH_LINE}/node" -v 2>/dev/null)
  case "$v" in
    v${NVMRC_MAJOR}.*) printf "   ok   %s -> %s\n" "$NODE_PATH_LINE" "$v" ;;
    *) printf "   FAIL %s -> %s (expected v%s.x)\n" "$NODE_PATH_LINE" "$v" "$NVMRC_MAJOR"; fail=$((fail+1)) ;;
  esac
else
  printf "   skip documented Homebrew path not present on this host (expected on CI/Linux)\n"
fi

echo ""
if [ "$fail" -gt 0 ]; then
  echo "FAIL: $fail README inaccuracy/ies. The README must match reality."
  exit 1
fi
echo "PASS: README commands, links, ports and Node path all verified against the repository."
exit 0
