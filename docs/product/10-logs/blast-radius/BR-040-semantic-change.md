---
blast_radius_id: BR-040
sub_step_id: STEP-004.09
title: Detect documented semantic change in the contract
author: Deepesh Kumar Gupta
date: 2026-08-13
score: LOW
confidence: HIGH
approval_required: false
---

# BR-040 — Documented semantic change

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `776e385` |
| HEAD at check | `776e385` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — additive to an existing tool; the gate's exit code is untouched |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(diff_contracts, upstream)` | `check_compatibility` and the contract tests — the expected two |
| 2 | **Measured the false-positive rate on the live corpus before choosing normalisation** | **0 of 54** described properties (§4) |
| 3 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

## 3. What this closes, and what it does not

`CONTRACT_CHANGE_POLICY` §1: *"Changing what a field means while keeping its name
and type passes every automated compatibility check and breaks every consumer."*
The `.08` classifier is structural and says so in its own docstring. This was the
one category in `REQ-PLAT-008` with **no automated coverage at all**.

**A semantic change is undetectable in general. A documented one is not.** An
author who changes what a field means and updates its description leaves a
machine-readable trace. This follows that trace and nothing else, which turns
"invisible" into "invisible only when undocumented" — strictly smaller, and not
closed.

An undocumented meaning change remains invisible. No tool fixes that, and the
sub-step says so rather than implying coverage it does not have.

## 4. The false-positive rate is measured, because `ENH-001` made that the condition

The enhancement was explicit: *"If the false-positive rate is not driven near zero
first, this should not ship."*

**Measured against the live corpus: 0 findings across 54 described properties.**

Three classes of edit change bytes without changing meaning, and normalisation
removes all three:

| Noise | Example | Handled by |
| --- | --- | --- |
| Reflow | a block scalar rewrapped | whitespace collapse |
| Emphasis | `must` → `**must**` | emphasis stripping |
| Code marks | `Money` → backticked | emphasis stripping |
| Sentence case | `Must` → `must` | case folding |

Each has its own test asserting **no** report. A typo fix still fires, and that is
accepted rather than engineered around: the report prints both texts so a reviewer
dismisses it at a glance, and guessing which edits are "trivial" is how a checker
starts silently ignoring real ones.

## 5. Why it reports instead of failing

This was the risk `ENH-001` costed, and the reason I recommended deferring it.

A check that fails the build on a reworded sentence is one people learn to bypass.
`BR-029` §3 records what that costs in this repository: `gitnexus_query` returns an
empty result that reads exactly like "no such concept exists", and the lesson was
that **a signal nobody can trust is worse than no signal**.

So the exit code is untouched — and a report nobody consumes is equally worthless,
which is why it is wired into `RELEASE_READINESS_CHECKLIST` §2 rather than left in
build output. It is resolved at the point a semantic change stops being free.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | `check_compatibility` gains one call |
| 2 | **Public API / contracts** | None. No contract changed |
| 3 | **Database / schema** | None |
| 4 | **Events** | None. AsyncAPI is still not diffed (`BR-035` §9) — unchanged here |
| 5 | **Configuration** | None. No new script |
| 6 | **Infrastructure** | None |
| 7 | **Security** | Indirect: a redefined field is how a permission or an error code changes meaning without any structural trace |
| 8 | **Privacy** | None |
| 9 | **Accessibility** | None |
| 10 | **Performance** | One pass over `components.schemas`; milliseconds |
| 11 | **Tenancy** | None |
| 12 | **Documentation** | This record, `IMPL-037`, the regression entry, `ENH-001` delivered, plus `CONTRACT_CHANGE_POLICY` §1 and `RELEASE_READINESS_CHECKLIST` §2 |

## 7. Data-flow inspection

No runtime flow. What is inspected is **the flow of a judgement** — from a
description edit to the human who must classify it.

| Hazard | Control | Evidence |
| --- | --- | --- |
| A meaning change reaching release unexamined | Reported with both texts | Seeded on the real contract; fires on `Evidenced.status` |
| The report firing on formatting, and being ignored | Four noise classes normalised away | One test each, all asserting **no** report |
| The report echoing structural changes | A property whose type or enum moved is skipped — already reported | Tested both halves |
| A green structural pass reading as a semantic pass | The PASS line names outstanding reviews explicitly | In the output |
| The report being printed and never consumed | `RELEASE_READINESS_CHECKLIST` §2 carries the checkbox | Wired |
| Silent degradation of the normaliser | The measured rate is a **test**, so if normalisation stops removing noise the suite fails | `test_the_false_positive_rate_is_measured_not_asserted` |
| A detector that reports nothing at all | A seeded real change must fire | `test_it_can_still_fire_on_the_real_contract` |

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Low | One report in one gate; no exit-code change |
| Reversibility | High | Delete one function and its call |
| Detectability | High | 9 tests, including the measured rate and a can-still-fire guard |
| Security exposure | None directly | Surfaces a class of change that would otherwise reach release unexamined |
| Performance | None | Milliseconds |
| **Overall** | **LOW** | **Confidence HIGH.** No owner approval required |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Contract suite | **65 passed** (up from 56) |
| Measured false positives | **0 of 54** described properties |
| Seeded semantic change | Detected, naming `Evidenced.status` |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
