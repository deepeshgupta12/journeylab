#!/usr/bin/env bash
# R7 as a gate in `pnpm verify` — STEP-001.07.
#
# WHY A WRAPPER RATHER THAN CALLING THE SUITE DIRECTLY
#   `tests/security/test_tenant_isolation.sh` uses three exit codes:
#
#       0  isolation verified
#       1  isolation BROKEN — SEV1
#       2  no database; nothing was evaluated
#
#   `pnpm verify` chains with `&&`, which treats 2 exactly like 1. Wiring the
#   suite in directly would therefore make `pnpm verify` fail on any machine
#   without `pnpm dev` running — turning the repository's headline command into
#   one that needs Docker before it can say anything about a CSS change.
#
#   The opposite mistake is worse: swallowing 2 makes a green `verify` mean
#   "isolation holds OR was never checked", which is how BUG-023 survived from
#   STEP-002.01 to STEP-001.07.
#
#   So the difference is made explicit here, in one place, rather than being an
#   emergent property of `&&`:
#
#       JOURNEYLAB_REQUIRE_DB set   -> a skip is a FAILURE (CI, ci-mirror)
#       unset                       -> a skip is tolerated, and says so LOUDLY
#
# Contract: exit 1 if isolation is broken, or if it could not be checked in an
# environment that declared a database.
# Run: bash tests/guards/tenant-isolation-gate.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

bash tests/security/test_tenant_isolation.sh
rc=$?

case "$rc" in
  0) exit 0 ;;
  2)
    if [ "${JOURNEYLAB_REQUIRE_DB:-0}" != "0" ] && [ -n "${JOURNEYLAB_REQUIRE_DB:-}" ]; then
      echo ""
      echo "FAIL: R7 did not run, and this environment declared a database."
      echo "      JOURNEYLAB_REQUIRE_DB is set, so a skip is a failure."
      exit 1
    fi
    echo ""
    echo '+------------------------------------------------------------------+'
    echo '|  R7 (cross-tenant isolation) DID NOT RUN — no database.            |'
    echo '|                                                                    |'
    echo '|  This is a SKIP, not a pass. Nothing here has verified that one    |'
    echo '|  tenant cannot read or revoke another'\''s rows.                      |'
    echo '|                                                                    |'
    # SINGLE quotes: inside double quotes bash treats backticks as command
    # substitution, so an earlier version of this line actually RAN `pnpm dev`
    # and started the whole Docker stack as a side effect of printing help text.
    echo '|  Run "pnpm dev" and re-run to actually check it. CI always does.   |'
    echo '+------------------------------------------------------------------+'
    exit 0
    ;;
  *) exit "$rc" ;;
esac
