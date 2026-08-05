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
for s in $(grep -oE 'pnpm [a-z][a-z:]*' "$README" | awk '{print $2}' | sort -u); do
  case "$s" in install|dlx|exec|add|remove) continue ;; esac
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
  for p in $(grep -oE '^\| 570[0-9] ' "$README" | tr -d '| '); do
    if grep -q "127.0.0.1:${p}:" "$COMPOSE"; then printf "   ok   %s\n" "$p"
    else printf "   FAIL %s documented but not published in compose\n" "$p"; fail=$((fail+1)); fi
  done
  for p in $(grep -oE '127\.0\.0\.1:[0-9]+:' "$COMPOSE" | grep -oE ':[0-9]+:' | tr -d ':' | sort -u); do
    if grep -qE "^\| $p \|" "$README"; then :
    else printf "   FAIL %s published in compose but undocumented in README\n" "$p"; fail=$((fail+1)); fi
  done
else
  printf "   FAIL %s missing\n" "$COMPOSE"; fail=$((fail+1))
fi

echo "4. documented Node PATH yields Node 24"
NODE_PATH_LINE=$(grep -oE '/opt/homebrew/opt/node@[0-9]+/bin' "$README" | head -1)
if [ -n "$NODE_PATH_LINE" ] && [ -x "${NODE_PATH_LINE}/node" ]; then
  v=$("${NODE_PATH_LINE}/node" -v 2>/dev/null)
  case "$v" in
    v24.*) printf "   ok   %s -> %s\n" "$NODE_PATH_LINE" "$v" ;;
    *)     printf "   FAIL %s -> %s (expected v24.x)\n" "$NODE_PATH_LINE" "$v"; fail=$((fail+1)) ;;
  esac
else
  printf "   FAIL documented Node path not executable: %s\n" "${NODE_PATH_LINE:-<none found>}"; fail=$((fail+1))
fi

echo ""
if [ "$fail" -gt 0 ]; then
  echo "FAIL: $fail README inaccuracy/ies. The README must match reality."
  exit 1
fi
echo "PASS: README commands, links, ports and Node path all verified against the repository."
exit 0
