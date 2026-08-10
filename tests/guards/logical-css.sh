#!/usr/bin/env bash
# Guard: RTL must stay a configuration change — STEP-003.07 (REQ-NFR-008).
#
# WHY THIS IS A GUARD AND NOT A TEST
#   Setting dir="rtl" flips every property expressed LOGICALLY
#   (inset-inline-start, margin-inline, padding-block) and flips nothing
#   expressed PHYSICALLY (left, margin-left, padding-right). A stylesheet that
#   mixes the two mirrors half the layout, which is worse than mirroring none of
#   it: the reading order and the controls disagree.
#
#   No unit test catches this, because both spellings render identically in the
#   LTR locale everyone develops in. The defect appears only in a language
#   nobody on the team reads, which is precisely when it will not be noticed.
#   So it is enforced at the source, on every commit.
#
# Contract: FAILS (exit 1) if a tracked or new CSS file uses a physical
# directional property. Run: bash tests/guards/logical-css.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git repository" >&2
  exit 2
fi

# Physical properties and their logical replacements.
#   margin-left/right      -> margin-inline-start/end
#   padding-left/right     -> padding-inline-start/end
#   border-left/right      -> border-inline-start/end
#   left:/right:           -> inset-inline-start/end
#   top:/bottom:           -> inset-block-start/end
#   text-align: left/right -> text-align: start/end
#   float: left/right      -> float: inline-start/inline-end
PHYSICAL='(margin|padding|border|scroll-margin|scroll-padding)-(left|right)[[:space:]]*:'
PHYSICAL="$PHYSICAL"'|(^|[^-[:alnum:]])(left|right|top|bottom)[[:space:]]*:'
PHYSICAL="$PHYSICAL"'|text-align[[:space:]]*:[[:space:]]*(left|right)'
PHYSICAL="$PHYSICAL"'|float[[:space:]]*:[[:space:]]*(left|right)'

hits=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$f" in
    *.css) ;;
    *) continue ;;
  esac
  # An explicit opt-out for the rare case where a physical edge is genuinely
  # meant (a hardware-anchored overlay, say). It must state a reason on the
  # SAME line, so the exemption is reviewable rather than invisible.
  if grep -nE "$PHYSICAL" "$f" | grep -v 'rtl-exempt:' >/dev/null 2>&1; then
    echo "PHYSICAL CSS: $f"
    grep -nE "$PHYSICAL" "$f" | grep -v 'rtl-exempt:' | head -5
    hits=$((hits + 1))
  fi
done < <(
  # BUG-004/BUG-010: tracked-only listing lets a brand-new file carrying the
  # defect pass on the run before its first commit.
  { git ls-files; git ls-files --others --exclude-standard; } | sort -u
)

if [ "$hits" -gt 0 ]; then
  echo ""
  echo "FAIL: $hits stylesheet(s) use physical directional properties."
  echo "Use the logical equivalents so dir=\"rtl\" mirrors the whole layout:"
  echo "  left/right       -> inset-inline-start / inset-inline-end"
  echo "  top/bottom       -> inset-block-start / inset-block-end"
  echo "  margin-left      -> margin-inline-start"
  echo "  padding-right    -> padding-inline-end"
  echo "  text-align: left -> text-align: start"
  echo "Genuinely physical? Add a same-line comment containing rtl-exempt: <reason>."
  exit 1
fi

css_count=$({ git ls-files; git ls-files --others --exclude-standard; } | sort -u | grep -c '\.css$' || true)
echo "PASS: $css_count stylesheet(s) use logical properties only."
exit 0
