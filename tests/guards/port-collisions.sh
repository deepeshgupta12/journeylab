#!/usr/bin/env bash
# Port collision guard — STEP-001.04
#
# JourneyLab owns the contiguous block 5700-5710. Multiple projects share this
# Docker host, so a collision is a real and recurring hazard.
#
# IMPORTANT: checks compose FILES of other projects, not just live sockets.
# A stopped project still owns its ports — 5544 looked free to `lsof` only
# because Saakshya was stopped at the time.
set -uo pipefail
cd "$(dirname "$0")/../.."

BLOCK_START=5700
BLOCK_END=5710
COMPOSE="docker-compose.dev.yml"

[ -f "$COMPOSE" ] || { echo "FAIL: $COMPOSE missing"; exit 1; }

# 1. Every published port must fall inside our block
outside=$(grep -oE '127\.0\.0\.1:[0-9]+:' "$COMPOSE" | grep -oE ':[0-9]+:' | tr -d ':' \
          | awk -v a=$BLOCK_START -v b=$BLOCK_END '$1<a || $1>b')
if [ -n "$outside" ]; then
  echo "FAIL: port(s) outside the reserved ${BLOCK_START}-${BLOCK_END} block:"
  echo "$outside" | sed 's/^/  /'
  exit 1
fi

# 2. No duplicate host ports within our own file
dupes=$(grep -oE '127\.0\.0\.1:[0-9]+:' "$COMPOSE" | sort | uniq -d)
if [ -n "$dupes" ]; then
  echo "FAIL: duplicate host port(s) in $COMPOSE:"; echo "$dupes" | sed 's/^/  /'; exit 1
fi

# 3. No other project on this host claims a port in our block
foreign=""
for f in $(find "$HOME" -maxdepth 4 -name 'docker-compose*.y*ml' 2>/dev/null | grep -v "$(pwd)"); do
  claimed=$(grep -oE '"[0-9]+:[0-9]+"' "$f" 2>/dev/null | grep -oE '^"[0-9]+' | tr -d '"' \
            | awk -v a=$BLOCK_START -v b=$BLOCK_END '$1>=a && $1<=b')
  [ -n "$claimed" ] && foreign="$foreign\n  $f: $(echo $claimed | tr '\n' ' ')"
done
if [ -n "$foreign" ]; then
  echo "FAIL: another project claims port(s) in our block:"; printf "$foreign\n"; exit 1
fi

count=$(grep -cE '127\.0\.0\.1:[0-9]+:' "$COMPOSE")
echo "PASS: $count published port(s), all within ${BLOCK_START}-${BLOCK_END}, no duplicates, no cross-project collision."
exit 0
