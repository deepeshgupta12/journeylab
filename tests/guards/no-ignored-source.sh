#!/usr/bin/env bash
# No source file may be git-ignored — STEP-007.02 (BUG-032).
#
# WHY THIS EXISTS
#   `.gitignore` had `coverage/` for test output. An unanchored directory pattern
#   matches at ANY depth, so it also ignored `apps/web/src/app/coverage/` — a
#   Next.js route directory.
#
#   The failure mode is what makes it worth a guard rather than a comment. The
#   files existed on disk, so the local build included the page and every local
#   test passed. `git add -A` skipped them silently. The commit looked complete.
#   CI built from the commit, had no page, and served 404 to every test that
#   touched it — and the only evidence was a route missing from a build manifest
#   in someone else's log.
#
#   Anchoring the pattern fixes today. This makes the next one fail here.
#
# Contract: FAILS (exit 1) if any file under a source tree is ignored.
# Meta-tested against a seeded ignored source file.
set -uo pipefail
cd "$(dirname "$0")/../.."

# Where source lives. Build output and caches are ignored on purpose and are not
# under these roots.
ROOTS=(apps/*/src packages/*/src services/*/src tools db/migrations contracts)

# BY EXTENSION, NOT BY LOCATION.
#   `__pycache__` sits inside every source tree and is ignored on purpose — it
#   holds `.pyc`, which is build output. Failing on "anything ignored under src"
#   would flag it and the guard would be muted within a day.
#
#   An ignored file whose extension is a SOURCE extension is the actual defect,
#   and `.pyc` does not match `\.py$`.
SOURCE_EXTENSIONS='\.(py|ts|tsx|js|jsx|mjs|cjs|sql|css|md)$'

scan() {
  local found=""
  for root in "${ROOTS[@]}"; do
    [ -d "$root" ] || continue
    local ignored
    ignored=$(git ls-files --others --ignored --exclude-standard "$root" 2>/dev/null \
              | grep -E "$SOURCE_EXTENSIONS" || true)
    [ -n "$ignored" ] && found="${found}${ignored}"$'\n'
  done
  printf '%s' "$found" | sed '/^$/d'
}

echo "=== scanning source trees for git-ignored files ==="
hits=$(scan)
if [ -z "$hits" ]; then
  echo "PASS: no file under a source tree is git-ignored."
else
  echo ""
  echo "FAIL: these are under a source tree and git is ignoring them:"
  echo "$hits" | sed 's/^/  /'
  echo ""
  echo "      They will build locally and be absent from the commit. Anchor the"
  echo "      .gitignore pattern that matches them — an unanchored directory"
  echo "      pattern matches at every depth (BUG-032)."
  exit 1
fi

# META-TEST: seed an ignored source file and confirm the scan rejects it.
echo ""
echo "=== META-TEST: a seeded ignored source file MUST fail the scan ==="
SEEDED="apps/web/src/app/coverage-report-seeded"
cleanup() {
  rm -rf "$SEEDED"
  sedi_restore
}
sedi_restore() {
  if [ -f /tmp/GITIGNORE_META.bak ]; then
    cp /tmp/GITIGNORE_META.bak .gitignore
    rm -f /tmp/GITIGNORE_META.bak
  fi
}
trap cleanup EXIT

cp .gitignore /tmp/GITIGNORE_META.bak
mkdir -p "$SEEDED"
echo "export const x = 1;" > "$SEEDED/page.tsx"
printf '\ncoverage-report-seeded/\n' >> .gitignore

if [ -z "$(scan)" ]; then
  echo "  FAIL: the scan passed with a seeded ignored source file — it is not detecting."
  exit 1
fi
echo "  ok   the scan rejects a seeded ignored source file"
exit 0
