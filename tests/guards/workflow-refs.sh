#!/usr/bin/env bash
# CI workflow reference guard — STEP-001.06
#
# A typo in a workflow only surfaces after a push, when the feedback loop is
# slowest. This validates locally that every workflow parses and that everything
# it references actually exists.
#
# Checks: YAML parses; referenced pnpm scripts exist; referenced guard scripts
# exist and are executable; version files referenced by setup actions exist.
set -uo pipefail
cd "$(dirname "$0")/../.."

WF=".github/workflows"
[ -d "$WF" ] || { echo "PASS (vacuous): no workflows yet."; exit 0; }

fail=0

# 1. YAML parses.
# BUG-008: previously reported "YAML does not parse" whenever `uv` was missing —
# a misleading error blaming the workflows for a toolchain gap. Distinguish the two.
if ! command -v uv >/dev/null 2>&1; then
  echo "  skip YAML parse check — uv not available on this host (real CI installs it)"
elif ! uv run --quiet python -c "import yaml" 2>/dev/null; then
  # BUG-016: this previously used `uv run --with pyyaml`, which FETCHES the package
  # at guard time. A transient network failure was then reported as "workflow YAML
  # does not parse" — blaming the workflows for a download problem, and making the
  # gate flaky. A flaky gate is worse than a failing one: it teaches people to
  # re-run rather than read. pyyaml is now a locked dev dependency, so this branch
  # means a genuinely broken environment, not a bad workflow.
  echo "  skip YAML parse check — pyyaml unavailable (run: uv sync). NOT a workflow problem."
elif ! uv run --quiet python -c "
import yaml,glob,sys
bad=0
for f in sorted(glob.glob('$WF/*.yml')):
    try: yaml.safe_load(open(f))
    except Exception as e: print('  INVALID YAML',f,e); bad=1
sys.exit(bad)
" 2>/dev/null; then
  echo "  FAIL: workflow YAML does not parse"; fail=$((fail+1))
else
  echo "  ok   all workflow YAML parses"
fi

# 2. pnpm scripts referenced exist (install/exec/dlx are built-ins)
for s in $(grep -rhoE 'pnpm [a-z][a-z:]*' "$WF" | awk '{print $2}' | sort -u); do
  case "$s" in install|exec|dlx|add|remove) continue ;; esac
  if node -e "process.exit(require('./package.json').scripts['$s']?0:1)" 2>/dev/null; then
    echo "  ok   pnpm $s"
  else
    echo "  FAIL pnpm $s referenced by a workflow but not in package.json"; fail=$((fail+1))
  fi
done

# 3. guard scripts referenced exist and are executable
for g in $(grep -rhoE 'tests/guards/[a-z-]+\.sh' "$WF" | sort -u); do
  if [ -x "$g" ]; then echo "  ok   $g"
  else echo "  FAIL $g referenced by a workflow but missing or not executable"; fail=$((fail+1)); fi
done

# 4. version files referenced by setup actions exist
for v in $(grep -rhoE '(node-version-file|python-version-file): [^ ]+' "$WF" | awk '{print $2}' | sort -u); do
  if [ -f "$v" ]; then echo "  ok   $v"
  else echo "  FAIL $v referenced by a workflow but does not exist"; fail=$((fail+1)); fi
done

echo ""
if [ "$fail" -gt 0 ]; then
  echo "FAIL: $fail broken workflow reference(s)."
  exit 1
fi
echo "PASS: all workflow references resolve."
exit 0
