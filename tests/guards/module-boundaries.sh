#!/usr/bin/env bash
# Module boundary enforcement + meta-test — STEP-001.02, revised under ADR-009.
#
# WHY THIS IS HAND-ROLLED RATHER THAN dependency-cruiser:
#   dependency-cruiser 18.1.1 (latest) supports typescript >=2 <7. Under the
#   TypeScript 7.0.2 pin (ADR-009) it cruised 0 modules and reported
#   "no dependency violations found" — a FALSE PASS. Boundary enforcement would
#   have silently become a no-op while reporting success. Caught by this script's
#   meta-test, which is the entire reason the meta-test exists.
#   Revisit dependency-cruiser when it supports TS 7 (upstream: "support for
#   typescript@>=7 will follow when its API is published and stable").
#
# Enforces ADR-003. Import paths are a *textual* property, so this check needs no
# TypeScript compiler API and cannot be silently disabled by a compiler upgrade.
#
# RULES (mirror .dependency-cruiser.cjs, retained as documentation of intent):
#   1. no-cross-module-internals  — importing another package's src/ internals
#   2. services-not-imported-by-web — apps/web must not import services/
#   3. no-generated-edits         — src/generated/ imported outside packages/contracts
#
# Contract: FAILS (exit 1) on any violation. Meta-tested against a seeded violation.
# Run: bash tests/guards/module-boundaries.sh
set -uo pipefail

cd "$(dirname "$0")/../.."

FIXTURE_A="packages/zz-boundary-fixture-a"
FIXTURE_B="packages/zz-boundary-fixture-b"
cleanup() { rm -rf "$FIXTURE_A" "$FIXTURE_B"; }
trap cleanup EXIT

# Emit "file:line:import-specifier" for every static/dynamic import and re-export.
collect_imports() {
  local scope="$1"
  find $scope -type f \( -name '*.ts' -o -name '*.tsx' \) 2>/dev/null \
    | grep -v '/node_modules/' \
    | while IFS= read -r f; do
        grep -nE "(from[[:space:]]+['\"]|import[[:space:]]*\(['\"]|require\(['\"])" "$f" 2>/dev/null \
          | sed -E "s|^([0-9]+):.*['\"]([^'\"]+)['\"].*|\1\t\2|" \
          | while IFS=$'\t' read -r line spec; do
              [ -n "${spec:-}" ] && printf '%s:%s\t%s\n' "$f" "$line" "$spec"
            done
      done
}

# owning package of a file path, e.g. packages/ui/src/x.ts -> packages/ui
owner_pkg() { echo "$1" | awk -F/ '{print $1"/"$2}'; }

check_scope() {
  local scope="$1" violations=0

  while IFS=$'\t' read -r loc spec; do
    [ -z "${loc:-}" ] && continue
    local file="${loc%:*}"
    local pkg; pkg="$(owner_pkg "$file")"
    local resolved=""

    # Resolve relative specifiers to a repo-root-relative path
    case "$spec" in
      ./*|../*)
        resolved="$(cd "$(dirname "$file")" 2>/dev/null && \
          python3 -c "import os,sys;print(os.path.relpath(os.path.normpath(os.path.join(os.getcwd(),sys.argv[1])),os.getcwd()))" "$spec" 2>/dev/null)"
        resolved="$(python3 -c "import os,sys;print(os.path.relpath(os.path.normpath(os.path.join(os.path.dirname(sys.argv[1]),sys.argv[2]))))" "$file" "$spec" 2>/dev/null)"
        ;;
      *) resolved="$spec" ;;
    esac

    # RULE 1: reaching into another package's internals
    case "$resolved" in
      apps/*/src/*|packages/*/src/*|services/*/src/*)
        local target_pkg; target_pkg="$(owner_pkg "$resolved")"
        if [ "$target_pkg" != "$pkg" ]; then
          echo "VIOLATION no-cross-module-internals"
          echo "  $loc"
          echo "  $pkg -> $target_pkg (via '$spec')"
          echo "  Packages expose entry points, not internals. See ADR-003."
          violations=$((violations + 1))
        fi
        ;;
    esac

    # RULE 2: web must not import services directly
    case "$file:$resolved" in
      apps/web/*:services/*)
        echo "VIOLATION services-not-imported-by-web"
        echo "  $loc -> $resolved"
        echo "  The web app talks to services over generated API clients only."
        violations=$((violations + 1))
        ;;
    esac

    # RULE 3: generated clients are private to packages/contracts
    case "$resolved" in
      *src/generated/*)
        case "$file" in
          packages/contracts/*) ;;
          *)
            echo "VIOLATION no-generated-edits"
            echo "  $loc -> $resolved"
            echo "  Generated clients are build artifacts (REQ-PLAT-007)."
            violations=$((violations + 1))
            ;;
        esac
        ;;
    esac
  done < <(collect_imports "$scope")

  return $violations
}

echo "=== 1. Boundary check over real source ==="
real_scope=""
for d in apps packages services; do [ -d "$d" ] && real_scope="$real_scope $d"; done
ts_count=$(find $real_scope -type f \( -name '*.ts' -o -name '*.tsx' \) 2>/dev/null | grep -vc '/node_modules/' || true)
if [ "${ts_count:-0}" -eq 0 ]; then
  echo "PASS (vacuous): no TypeScript source yet — rule applies from STEP-002 onward."
else
  if check_scope "$real_scope"; then
    echo "PASS: $ts_count file(s) respect module boundaries."
  else
    echo ""
    echo "FAIL: boundary violation(s) in real source."
    exit 1
  fi
fi

echo ""
echo "=== 2. META-TEST: rule must fire on a deliberate violation ==="
mkdir -p "$FIXTURE_A/src" "$FIXTURE_B/src"
printf '{ "name": "zz-a", "version": "0.0.0", "private": true, "type": "module" }\n' > "$FIXTURE_A/package.json"
printf '{ "name": "zz-b", "version": "0.0.0", "private": true, "type": "module" }\n' > "$FIXTURE_B/package.json"
printf "export const privateHelper = (): string => 'internal';\n" > "$FIXTURE_A/src/internal.ts"
printf "export { privateHelper } from './internal.js';\n" > "$FIXTURE_A/src/index.ts"
# DELIBERATE VIOLATION: reaches into package A's internals
printf "import { privateHelper } from '../../zz-boundary-fixture-a/src/internal.js';\nexport const useIt = (): string => privateHelper();\n" > "$FIXTURE_B/src/index.ts"

meta_out=$(check_scope "$FIXTURE_B" 2>&1)
meta_rc=$?

if echo "$meta_out" | grep -q 'no-cross-module-internals' && [ "$meta_rc" -gt 0 ]; then
  echo "PASS: rule 'no-cross-module-internals' fired on the seeded violation ($meta_rc violation(s))."
  cleanup
  exit 0
fi

echo "FAIL: seeded boundary violation was NOT caught."
echo "  violations reported: $meta_rc"
echo "--- output ---"
echo "$meta_out" | head -20
cleanup
exit 1
