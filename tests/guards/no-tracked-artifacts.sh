#!/usr/bin/env bash
# Regression guard for BUG-002 — build artifacts / dependencies tracked in git.
#
# BUG-002: `node_modules/` was committed because .gitignore contained only
# `.gitnexus`. Found by the STEP-001.02 pre-change analysis, not by any test —
# this guard closes that gap.
#
# Contract: FAILS (exit 1) if any tracked path is a dependency or build artifact.
set -uo pipefail
cd "$(dirname "$0")/../.."

# BUG-014: this list is a DENYLIST, so it only ever catches artifacts someone
# thought of in advance. `.vexp/` — a tool's private SQLite index — sailed through
# it and 9.2 MB was committed. Names are still checked, but two shape-based rules
# below catch the class rather than the instance.
FORBIDDEN='^(node_modules|dist|build|\.next|\.venv|coverage|htmlcov|\.vexp|\.turbo|\.cache|\.pytest_cache|\.ruff_cache|\.mypy_cache)/|(^|/)__pycache__/|\.pyc$|(^|/)\.env$|(^|/)\.DS_Store$'
# BUG-004: check untracked-but-stageable paths too, not just tracked ones.
hits=$({ git ls-files; git ls-files --others --exclude-standard; } | sort -u | grep -E "$FORBIDDEN" || true)
if [ -n "$hits" ]; then
  echo "TRACKED ARTIFACTS (BUG-002 regression):"
  echo "$hits" | head -20
  echo ""
  echo "FAIL: $(echo "$hits" | wc -l | tr -d ' ') forbidden path(s) tracked in git."
  exit 1
fi
# SECRETS: private key material must never be tracked, regardless of .gitignore.
# .gitignore protects against accident; this protects against `git add -f` and
# against someone "fixing" .gitignore later without understanding why.
KEY_SHAPE='\.(pem|key|p12|pfx|jks|keystore)$'
key_hits=$({ git ls-files; git ls-files --others --exclude-standard; } | sort -u | grep -E "$KEY_SHAPE" || true)
if [ -n "$key_hits" ]; then
  echo "TRACKED KEY MATERIAL:"
  echo "$key_hits" | head -20
  echo "FAIL: private key or certificate material is tracked. Remove it and rotate."
  exit 1
fi

# SHAPE: embedded databases and their sidecars are never shared state.
DB_SHAPE='\.(db|sqlite|sqlite3)(-wal|-shm|-journal)?$|(^|/)index\.lock$'
db_hits=$({ git ls-files; git ls-files --others --exclude-standard; } | sort -u | grep -E "$DB_SHAPE" || true)
if [ -n "$db_hits" ]; then
  echo "TRACKED DATABASE FILES (BUG-014):"
  echo "$db_hits" | head -20
  echo "FAIL: an embedded database or lock sidecar is tracked."
  exit 1
fi

# SIZE: the real generalisation. The largest legitimate file in this repository is
# ~31 KB of Markdown; the accidental commit was 9.2 MB. Anything approaching a
# megabyte is a binary nobody reviewed.
MAX_BYTES=524288
big=""
while IFS= read -r f; do
  [ -f "$f" ] || continue
  size=$(wc -c <"$f" | tr -d ' ')
  [ "$size" -gt "$MAX_BYTES" ] && big="$big$size  $f\n"
done <<EOF
$( { git ls-files; git ls-files --others --exclude-standard; } | sort -u )
EOF
if [ -n "$big" ]; then
  echo "OVERSIZED TRACKED FILE(S) (BUG-014) — limit ${MAX_BYTES} bytes:"
  printf "%b" "$big" | head -10
  echo "FAIL: a large binary is tracked. If it is genuinely required, raise MAX_BYTES"
  echo "      deliberately and say why — do not let it through silently."
  exit 1
fi

echo "PASS: no dependency or build artifacts ($({ git ls-files; git ls-files --others --exclude-standard; } | sort -u | wc -l | tr -d ' ') files checked)."
exit 0
