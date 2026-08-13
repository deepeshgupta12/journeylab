#!/usr/bin/env bash
# Guard: a carried commitment cannot outlive its target — STEP-001.08 (ENH-002).
#
# BUG-022: STEP-002.05 carried session revocation to STEP-002.07; .07 closed
# VERIFIED without it and nothing failed, because a carry is prose and
# substep-docs.sh only checks that records EXIST, not that promises inside them
# were kept.
#
# Contract: FAILS (exit 1) when a carry names an already-VERIFIED sub-step and
# the line carries no disposition.
# Run: bash tests/guards/carried-commitments.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

exec uv run python tools/carried_commitments.py
