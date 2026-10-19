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
# A SECOND RULE, FOUND THE HARD WAY — BUG-039
#   A probe that can time out is a probe that can be orphaned. When a CMD-SHELL health
#   check exceeds its timeout, Docker kills the shell and the `pg_isready` it spawned is
#   reparented to PID 1. If PID 1 is the postmaster, it sees an untracked child exit 2
#   ("no response" — the reason it was slow) and treats that as a crash: every backend
#   is terminated. The dev database killed itself twice in seventy seconds under the
#   browser suite's load. So every file that defines a pg_isready probe must also give
#   its container an init process (`init: true` in compose, `--init` for docker run and
#   for a CI service's options), and orphans are reaped by init instead. Only probes
#   used AS a health check are in scope — a wait loop has no timeout that kills it.
#
# Contract: FAILS (exit 1) if any pg_isready health check omits an explicit host
#           (SOCKET PROBE), or lives in a file that gives its container no init
#           process (NO INIT).
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

# BUG-039: the container running each probe must have an init process. Checked per
# FILE: a compose file must declare `init: true`; a shell script or workflow must pass
# `--init`. Coarser than per-service on purpose — a file that defines a probe and no
# init anywhere is wrong, and the finer check would be a YAML parser in bash.
# Only probes that run AS A CONTAINER HEALTH CHECK are in scope here: a compose
# `test:` or a `--health-cmd`. Those are the ones Docker kills on timeout, which is
# what orphans the probe onto PID 1. A pg_isready in a wait loop (`docker exec`, or
# run from the host, as tests/e2e/smoke.sh does) has no health timeout, is never
# reparented to the postmaster, and is not the hazard — the first version of this
# rule flagged it anyway, and a rule that is wrong about one file is a rule people
# learn to override.
healthchecks=$(echo "$matches" | grep -E "health-cmd|[[:space:]]test:[[:space:]]*\[" || true)
noinit=0
for file in $(echo "$healthchecks" | cut -d: -f1 | sort -u); do
  [ -z "$file" ] && continue
  case "$file" in
    *.yml|*.yaml)
      # Comment lines are stripped first. The first version of this check was
      # satisfied by its own explanatory comment ("BUG-039: --init, so ...") after the
      # real flag had been removed — the meta-suite caught it. A flag in a comment
      # reaps nothing.
      if echo "$file" | grep -q "/workflows/"; then
        grep -vE "^[[:space:]]*#" "$file" | grep -qE -- "--init" || { echo "  NO INIT: $file (CI service options need --init)"; noinit=$((noinit + 1)); }
      else
        grep -qE "^[[:space:]]+init:[[:space:]]*true" "$file" || { echo "  NO INIT: $file (compose service needs init: true)"; noinit=$((noinit + 1)); }
      fi ;;
    *.sh)
      grep -vE "^[[:space:]]*#" "$file" | grep -qE -- "--init" || { echo "  NO INIT: $file (docker run needs --init)"; noinit=$((noinit + 1)); } ;;
  esac
done

if [ "$noinit" -gt 0 ]; then
  echo ""
  echo "FAIL: $noinit file(s) define a pg_isready probe in a container with no init process."
  echo ""
  echo "  When the probe times out, Docker kills its shell and the orphaned pg_isready"
  echo "  is reparented to PID 1. If that is the postmaster, an exit code of 2 is"
  echo "  treated as a crash and every backend is terminated (BUG-039, BR-068)."
  echo ""
  echo "  Give the container an init: \`init: true\` (compose) or \`--init\` (docker run,"
  echo "  CI service options)."
  exit 1
fi

total=$(echo "$matches" | grep -c . || true)
echo "PASS: all $total pg_isready probe(s) use an explicit host (BUG-009/BUG-025) in a container with an init process (BUG-039)."
exit 0
