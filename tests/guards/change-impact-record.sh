#!/usr/bin/env bash
# Change-impact record gate — STEP-001.06, enforcing REQ-KG-008.
#
# "No code, schema, API, event, model, prompt, infrastructure or configuration
#  change may begin until the pre-change impact analysis is complete and recorded."
#
# Until now that rule was procedural — followed because someone remembered. This
# makes it MECHANICAL: a substantive change without a blast-radius record fails.
#
# WHY A SCRIPT RATHER THAN WORKFLOW YAML:
#   GitHub Actions cannot be run locally, so a gate written only as YAML would be
#   unverifiable until a PR exercised it. BUG-004 was exactly that shape — a guard
#   trusted before its scope was tested. The logic lives here, meta-testable now;
#   .github/workflows/change-impact.yml is a thin caller.
#
# USAGE
#   bash tests/guards/change-impact-record.sh              # working tree vs HEAD
#   bash tests/guards/change-impact-record.sh <base_ref>   # CI: diff against base
#
# EXEMPT (deliberate — a gate that blocks everything gets disabled, and a disabled
# gate is worse than none):
#   - documentation, logs and blast-radius records themselves
#   - the generated GitNexus context files
#   - lock-file-only refreshes with no manifest change
set -uo pipefail
cd "$(dirname "$0")/../.."

BASE="${1:-}"
BRDIR="docs/product/10-logs/blast-radius"

if [ -n "$BASE" ]; then
  changed=$(git diff --name-only "$BASE"...HEAD 2>/dev/null)
  scope="$BASE...HEAD"
else
  changed=$( { git diff --name-only HEAD; git diff --cached --name-only;
               git ls-files --others --exclude-standard; } | sort -u )
  scope="working tree"
fi

if [ -z "${changed:-}" ]; then
  echo "PASS: no changes in $scope — nothing to gate."
  exit 0
fi

# Substantive = anything that is not documentation, logs or generated context.
substantive=$(echo "$changed" | grep -vE '^docs/' \
  | grep -vE '^(CLAUDE|AGENTS)\.md$' \
  | grep -vE '^(README|SECURITY|CONTRIBUTING)\.md$' \
  | grep -vE '^\.gitnexus/' || true)

if [ -z "${substantive:-}" ]; then
  echo "PASS: $scope contains documentation-only changes — exempt by policy."
  echo "      ($(echo "$changed" | wc -l | tr -d ' ') file(s) changed, 0 substantive)"
  exit 0
fi

# Lock-file-only refresh with no manifest change is exempt.
non_lock=$(echo "$substantive" | grep -vE '(pnpm-lock\.yaml|uv\.lock)$' || true)
if [ -z "${non_lock:-}" ]; then
  echo "PASS: lock-file refresh only — exempt by policy."
  exit 0
fi

echo "Substantive change(s) detected in $scope:"
echo "$substantive" | sed 's/^/  /' | head -20

# A blast-radius record must exist AND have been touched alongside the change.
if [ -n "$BASE" ]; then
  br_touched=$(git diff --name-only "$BASE"...HEAD -- "$BRDIR" 2>/dev/null | grep -E 'BR-[0-9]{3}' || true)
else
  br_touched=$( { git diff --name-only HEAD -- "$BRDIR"; git diff --cached --name-only -- "$BRDIR";
                  git ls-files --others --exclude-standard -- "$BRDIR"; } | sort -u | grep -E 'BR-[0-9]{3}' || true)
fi

if [ -z "${br_touched:-}" ]; then
  echo ""
  echo "FAIL: substantive change with NO blast-radius record (REQ-KG-008)."
  echo ""
  echo "  Before changing code, schema, contracts, models, prompts, infrastructure"
  echo "  or configuration, complete a pre-change impact analysis:"
  echo "    docs/product/05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md"
  echo "  Then record it as $BRDIR/BR-NNN-<slug>.md"
  echo "    template: docs/product/09-templates/CHANGE_IMPACT_TEMPLATE.md"
  echo ""
  echo "  If the graph is BLOCKED, say so in the record and apply the static"
  echo "  fallback — an honest BLOCKED is acceptable; a missing record is not."
  exit 1
fi

echo ""
echo "Blast-radius record(s) present:"
echo "$br_touched" | sed 's/^/  /'

# Each record must carry the graph-state section the protocol requires.
missing=0
for f in $br_touched; do
  [ -f "$f" ] || continue
  grep -qiE 'graph indexed commit|indexed commit' "$f" || { echo "  INCOMPLETE $f — no graph-state section"; missing=$((missing+1)); }
  grep -qiE 'overall:|\*\*Overall' "$f" || { echo "  INCOMPLETE $f — no risk score"; missing=$((missing+1)); }
done

if [ "$missing" -gt 0 ]; then
  echo ""
  echo "FAIL: $missing incomplete record(s) — a record must state graph state and a risk score."
  exit 1
fi

echo ""
echo "PASS: substantive changes are covered by a complete blast-radius record."
exit 0
