#!/usr/bin/env bash
# Guard: every Postgres health check is a TCP check — BUG-009, re-broken as BUG-025.
#
# WHY THIS EXISTS RATHER THAN A COMMENT
#   BUG-009 (STEP-002.02) established that the official Postgres entrypoint runs a
#   TEMPORARY, socket-only server during first-boot initialisation. A default
#   `pg_isready` talks to that socket, so it reports READY against a server that is
#   about to be shut down and restarted. Anything waiting on it proceeds too early.
#
#   The fix went into docker-compose.dev.yml with a warning comment. Then
#   STEP-001.07 added a Postgres service to CI and to the mirror and wrote the
#   socket form in BOTH — because a comment in one file cannot stop a second file
#   being written. That is BUG-025, and it is the third appearance of BUG-009.
#
#   R6 keeps every closed bug's regression test passing. BUG-009 had no test that
#   generalised: it had a fixed compose file. This is that test.
#
# Contract: FAILS (exit 1) if any pg_isready health check omits an explicit host.
# Run: bash tests/guards/postgres-healthcheck.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

# Only lines where pg_isready is used AS a health/readiness probe. A bare
# `pg_isready` run by a human at a prompt is not a gate and is not the hazard.
matches=$(grep -rn "pg_isready" \
            --include="*.yml" --include="*.yaml" --include="*.sh" \
            . 2>/dev/null | grep -v "^./node_modules" | grep -v "postgres-healthcheck.sh") || true

bad=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  case "$line" in
    *"#"*pg_isready*) continue ;;   # a comment explaining the rule
  esac
  # The hazard is a probe with no host: it defaults to the Unix socket.
  if ! echo "$line" | grep -qE "pg_isready[^|]*-h[[:space:]]"; then
    echo "  SOCKET PROBE: $line"
    bad=$((bad + 1))
  fi
done <<< "$matches"

if [ "$bad" -gt 0 ]; then
  echo ""
  echo "FAIL: $bad pg_isready probe(s) use the Unix socket."
  echo ""
  echo "  During first-boot init the entrypoint runs a TEMPORARY socket-only"
  echo "  server. A socket probe reports READY against a server that is about to"
  echo "  be destroyed, so whatever waits on it proceeds too early (BUG-009)."
  echo ""
  echo "  Use the TCP form:  pg_isready -h 127.0.0.1 -U <user>"
  exit 1
fi

total=$(echo "$matches" | grep -c . || true)
echo "PASS: all $total pg_isready probe(s) use an explicit host (BUG-009/BUG-025)."
exit 0
