#!/usr/bin/env bash
# Guard: no breaking contract change without a major version bump — STEP-004.08.
#
# REQ-PLAT-008 · CONTRACT_CHANGE_POLICY §4
#
# The classification logic is tools/contract_diff.py and the decision is
# tools/check_compatibility.py. This file exists so the check has the same shape as
# every other gate in tests/guards/ — one script, exit 0 or 1, runnable alone.
#
# Contract: FAILS (exit 1) on a breaking diff against contracts/baseline/ that is
# not carried by a major version bump, on a deprecated operation with no Sunset
# header, or on a baseline snapshot moved without declaring the release.
#
# Run: bash tests/guards/contract-compatibility.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

exec uv run python tools/check_compatibility.py
