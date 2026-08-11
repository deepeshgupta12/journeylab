---
sub_step_id: STEP-003.09
parent_step: STEP-003
title: Visual design language
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-004, REQ-NFR-007, REQ-NFR-013]
blast_radius_id: BR-026
depends_on: [STEP-003.08]
last_updated: 2026-08-11
---

# STEP-003.09 — Visual design language

## 1. Outcome
The product looks designed rather than defaulted, without giving back any of the
accessibility guarantees `.08` established.

## 2. Why this sub-step exists at all

It was not in the original plan, and that was the gap.

`STEP-003.01` delivered accessible **tokens**. `.02`–`.07` delivered
**behaviour**. `.08` delivered the **accessibility floor** — target sizes,
contrast, focus rings — because until then 28 of the design system's 40 class
names had no CSS whatsoever.

Nothing delivered **design**. The owner reviewed the `.08` screenshots and said
so plainly. They were right: the result was legible, operable, standards-clean
and looked like an unstyled document, because in most respects it was one.

Direction was delegated to the implementer with the brief "use your judgement".
What that judgement produced, and why, is §5.

## 3. Scope and boundary

**In scope:** `packages/ui/src/tokens.ts` (colour, radius, type, elevation
scales); `packages/ui/src/components.css`; `apps/web/src/app/shell.css`;
gallery presentation.

**Not in this sub-step:** iconography (the status tokens name icons that nothing
renders yet); illustration; motion design beyond the existing reduced-motion
contract; marketing surfaces; a logo.

## 4. Pre-change analysis

| Field | Value |
| --- | --- |
| Graph status | ✅ **NOT BLOCKED** — `npx gitnexus status` up to date |
| HEAD / indexed commit | `3793494` / `3793494` — matched |
| Queries run | `impact(contrastPairs)` → 1 direct (`tokens.test.ts`), LOW, `exact`; `impact(renderCss)` → 2 direct, LOW, `exact`; `detect_changes()` |
| Unknown / low-confidence areas | The graph still cannot trace JSX usage (`BR-025` §3), so component reach is established by the compiler and by the 40-test browser suite rather than by the graph |
| Blast radius | **[BR-026](../../../10-logs/blast-radius/BR-026-visual-design.md) — MEDIUM, confidence HIGH** |
| Approval required? | **No** — MEDIUM with high confidence, fully reversible |

## 5. The design decisions, and the reasoning

**Restraint, because of what the product does.** JourneyLab shows which futures
are feasible and the evidence behind each. The interface is a reading surface
for decisions someone will act on, sometimes under pressure, sometimes on a
phone in an unfamiliar place. That argues for hierarchy over decoration, colour
reserved for meaning, density that stays legible, and calm.

| Decision | Reasoning |
| --- | --- |
| **Warm neutrals**, not blue-grey | The old ramp was the default palette of every developer tool. The content here is places and times of day. The hue moved; the luminance did not, so no contrast ratio regressed |
| **Three border weights** (`subtle`, `default`, `strong`) | One border colour meant a hairline between table rows shouted as loudly as the outline of a text input. That is why `.08` looked like a wireframe |
| **Status surface tints** | A tinted panel reads faster than a coloured edge alone. Each tint is a declared token with its own contrast pairs, so it cannot be chosen because it looked nice — text on it is asserted at 4.5:1 |
| **A radius scale** | Everything used `--space-1` (4px), so a text input and a full-screen dialog had the same corner. Radius should scale with the element |
| **A system font stack, as a decision** | Not a placeholder for a webfont. A webfont costs a request on the critical path and either blocks paint or swaps mid-read — both damage LCP, which `.08` now gates. It also fails exactly when a traveller most needs the page |
| **Optical tracking and a 65ch measure** | Large text needs negative tracking, small text positive; without it a size scale reads as one font at several sizes rather than as a family |
| **Two-layer shadows** | A single blurred shadow reads as a smudge. Real objects cast a tight contact shadow and a wider ambient one |
| **Tabular figures** | Times and prices in a column must not shuffle sideways as digits change |
| **Sticky header, centred 72rem measure** | The nav is how you leave a page; hunting for it by scrolling up is a small cruelty. Full-width text on a 27-inch display is unreadable |

## 6. Contracts and schema changes
None. No API, event or schema surface is touched.

## 7. Tests

| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| `tokens.test.ts` | unit | Every declared pair meets its WCAG minimum, **including the 12 new status-tint pairs** | ✅ 307 UI tests |
| — | unit | A new status *signal* colour still requires an icon and label; a `-surface` tint does not | ✅ added, with a test proving the exclusion did not turn the rule off |
| `a11y.spec.ts` | browser | The full `.08` gate, unchanged | ✅ 40 passed |
| `logical-css.sh` | guard | No physical directional properties | ✅ |

**No new test file.** That is deliberate: the point of doing `.08` first was that
the design pass would be policed by the gate that already existed. It was —
three times (§10).

## 8. Telemetry, security and accessibility
No new data flow, no new input, no new stored field. Accessibility is
**unchanged by contract and improved in practice**: the same 40 assertions pass,
and the status tints add 12 new contrast pairs that are now proven rather than
assumed.

## 9. Documentation to update
- [x] This record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) — IMPL-023
- [x] [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md)
- [x] [BR-026](../../../10-logs/blast-radius/BR-026-visual-design.md)
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **N/A** | No contracts. Tokens gained keys; none removed |
| R3 graph diff as expected | **PASS** | Palette constants, `contrastPairs`, `renderCss` and the two stylesheets |
| R4 untested requirements | **PASS** | 12 new contrast pairs newly proven |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers all changed paths |
| R6 closed-bug regression tests | **PASS** | BUG-001…018; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** **PASS**

### The gate caught the design pass three times
This is the finding worth keeping.

1. **Checkbox and radio shrunk to 20px.** 20 looks better beside 14px label text.
   SC 2.5.8 is 24×24, and a checkbox is its own target regardless of the 44px row
   it sits in. Rejected within one run.
2. **2px of horizontal overflow at 320px.** A grid item defaults to
   `min-width: auto` and refuses to shrink below its widest unbreakable word; one
   long place name in the list widened the track, the track widened the document.
3. **A leftover `margin: -1px`** on the visually-hidden pattern, from the older
   `clip: rect()` technique, putting the skip link at `x = -1`.

A fourth failure was the INP check reporting 422 ms once on a busy machine and
7 ms when idle — a flaky gate, which `BUG-016` already established is worse than
a failing one. It now takes the median of five interactions.

## 11. Rollback
Revert this sub-step's commit. Tokens and stylesheets are the only surfaces
touched; no data, no schema, no contract.

## 12. Acceptance criteria
- [x] The product reads as designed, not defaulted
- [x] Every `.08` accessibility assertion still passes — 40/40
- [x] Dark and high-contrast themes still work
- [x] New colour tokens are contrast-proven, not asserted in a comment
- [x] No webfont, so no LCP or FOIT cost
- [x] RTL unaffected — logical properties throughout

## 13. Completion record

| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None new. Three design regressions caught by the `.08` gate before commit |
| Notes / surprises | **Doing accessibility before design was the right order, and this sub-step is the evidence.** Three of the changes made here would have shipped as defects in any other sequence — the 20px checkbox in particular is the kind of thing that looks better, tests fine by hand, and quietly fails a standard.<br><br>The 12 new contrast pairs matter more than the tints they justify. A tinted panel is the easiest place in a design system to lose contrast, because the tint is chosen for feel and the text colour is inherited from somewhere else. Declaring each tint as a background with its own asserted minimum makes that impossible rather than unlikely.<br><br>An existing test failed correctly and had to be *sharpened rather than loosened*: the status-token coverage rule caught the new `-surface` tokens and demanded an icon for each. A tint is not a signal, so the rule now excludes the `-surface` suffix — and a second test asserts a hypothetical new signal colour is still caught, because the easy fix would have made the whole check vacuous. |
