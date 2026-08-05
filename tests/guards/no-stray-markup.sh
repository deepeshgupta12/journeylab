#!/usr/bin/env bash
# Regression guard for BUG-001 — stray authoring markup in committed files.
#
# BUG-001: 110 files were committed containing a literal closing-tag line, an
# artifact of the authoring tool's file-write wrapper leaking into file bodies.
# It made package.json invalid JSON and would have made every generated config
# file unparseable.
#
# NOTE ON THIS FILE: the offending patterns are ASSEMBLED AT RUNTIME rather than
# written literally. A first attempt at this guard embedded the literal tag and
# truncated its own source file — the bug reproduced itself inside its own test.
# Keep the assembly; do not "simplify" it to a literal string.
#
# Contract: FAILS (exit 1) if any tracked file contains a stray tag line.
# Run: bash tests/guards/no-stray-markup.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

LT='<'
SL='/'
GT='>'
# Line consisting solely of a closing tag for a wrapper element.
PATTERN="^${LT}${SL}(content|parameter|antml:parameter|antml:invoke|function_results)${GT}$"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git repository" >&2
  exit 2
fi

hits=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$f" in
    tests/guards/no-stray-markup.sh) continue ;;  # this file documents the pattern
  esac
  if grep -nE "$PATTERN" "$f" >/dev/null 2>&1; then
    echo "STRAY MARKUP: $f"
    grep -nE "$PATTERN" "$f" | head -3
    hits=$((hits + 1))
  fi
done < <(git ls-files)

if [ "$hits" -gt 0 ]; then
  echo ""
  echo "FAIL: $hits file(s) contain stray authoring markup (BUG-001 regression)."
  exit 1
fi

echo "PASS: no stray authoring markup in $(git ls-files | wc -l | tr -d ' ') tracked files."
exit 0
