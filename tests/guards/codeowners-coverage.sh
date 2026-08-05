#!/usr/bin/env bash
# CODEOWNERS coverage guard — STEP-001.03 (REQ-PLAT-003)
# Every tracked path must resolve to an owner. Requires a catch-all rule.
set -uo pipefail
cd "$(dirname "$0")/../.."
[ -f CODEOWNERS ] || { echo "FAIL: CODEOWNERS missing (REQ-PLAT-003)"; exit 1; }
if ! grep -qE '^\*[[:space:]]+@' CODEOWNERS; then
  echo "FAIL: no catch-all rule in CODEOWNERS — some paths would be unowned."
  exit 1
fi
owners=$(grep -cE '^[^#[:space:]]+[[:space:]]+@' CODEOWNERS)
echo "PASS: CODEOWNERS has a catch-all and $owners ownership rule(s); all $(git ls-files | wc -l | tr -d ' ') tracked paths resolve to an owner."
exit 0
