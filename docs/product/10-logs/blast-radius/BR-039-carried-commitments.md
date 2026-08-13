---
blast_radius_id: BR-039
sub_step_id: STEP-001.08
title: A carried commitment cannot be dropped silently
author: Deepesh Kumar Gupta
date: 2026-08-13
score: LOW
confidence: HIGH
approval_required: false
---

# BR-039 — Carried-commitment guard

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `34588be` |
| HEAD at check | `34588be` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — documentation and one new guard; no runtime surface |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | A read-only prototype over 51 sub-step records and every log, **before writing anything** | 20 carries across sub-steps, logs and blast radii. **The results changed the design twice** (§3) |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

## 3. The prototype was worth more than the guard

Running a throwaway detector first, against the real corpus, killed two designs
that would both have shipped and both been wrong.

### "The target must mention the source" does not survive contact

`STEP-004.01` carried the `auth/errors.py` RFC 9457 migration to `STEP-004.04`.
`.04` dealt with it properly — by establishing the carry was **mistaken**: *"I said
in a hand-off that `auth/errors.py` migrates to RFC 9457 here… Neither is true."*
It never names `.01`.

Discharge has three honest shapes — **done**, **withdrawn**, **re-routed** — and
only the first looks like doing the work. A mention-based check fails two of three
and teaches people to game it.

### The prototype flagged work I had already fixed

`.04` and `.05` reported as dropped, because `STEP-002.08` rewrote those lines to
**quote** the old carry while explaining the fix. A live promise and a historical
quotation of one are textually identical.

That is precisely the false-positive class `ENH-002` predicted, and it is why the
disposition lives **on the carry line**: the person who resolves a promise annotates
the promise, and a quotation is not a promise.

## 4. What it found

Six carries pointed at already-closed sub-steps. Five were genuine discharges
needing only annotation. **One was a live commitment with no home:**

> `auth/errors.py` still returns the STEP-002.02 shape, not RFC 9457. `STEP-004.01`
> carried the migration to `.04`; `.04` correctly established it was not its job —
> **and nobody re-carried it.** Two error shapes have coexisted in the repository
> since STEP-004.01, drifting, with the record pointing at a sub-step that had
> declined it.

Now annotated `— superseded: re-carried to STEP-008`, where the first route
handlers land. Not a new bug — `BR-028` §7 disclosed the two shapes at the time —
but the *ownership* had been lost, which is what `BUG-022` was.

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None. A standalone tool and a shell wrapper |
| 2 | **Public API / contracts** | None |
| 3 | **Database / schema** | None |
| 4 | **Events** | None |
| 5 | **Configuration** | `verify` gains a step, placed next to `guard:substep-docs` — the check it complements |
| 6 | **Infrastructure** | None |
| 7 | **Security** | Indirect and the reason this exists: the commitment BUG-022 lost was a **security control** |
| 8 | **Privacy** | None |
| 9 | **Accessibility** | None |
| 10 | **Performance** | ~1s over 208 documents |
| 11 | **Tenancy** | None |
| 12 | **Documentation** | Six annotations, `WAYS_OF_WORKING` gains the convention, plus this record, `IMPL-036`, the regression entry, `ENH-002` delivered |

## 6. Data-flow inspection

No data flow. What is inspected is **the flow of a promise** — from the record that
defers it to the record that should resolve it.

| Hazard | Control | Evidence |
| --- | --- | --- |
| A deferral outliving its target | Fail when the target is `VERIFIED` and the line is silent | Seeded with the BUG-022 shape; killed |
| A guard that fires either way | A disposed carry must **pass** | Seeded; passes |
| A normal deferral treated as a defect | Only `VERIFIED` targets are checked | Seeded with an open target; passes |
| The guard failing on its own documentation | `STEP-NNN` placeholders skipped, plus an explicit `carry-exempt` marker | Seeded; passes. **It fired on its own docs five times before this was right** |
| Re-routing used to escape the check | `— superseded by` is a valid disposition **and is written down**, so a promise that keeps moving is countable | By construction; §4 is the first instance |
| A dishonest disposition | **Not prevented.** §7 |

## 7. The honest limit

It proves a carry was **considered at closure**, not that the work was **done**.
`— withdrawn: nonsense` passes.

That is the same limit as `contracts/baseline/BASELINE.md` §3, and it is stated for
the same reason: the check converts silence into a specific, recorded, reviewable
claim. It cannot make the claim true. A guard that pretended otherwise would be a
worse guard, because someone would trust it.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Low | Documentation and one guard; nothing at runtime |
| Reversibility | High | Delete the guard; the annotations are harmless prose |
| Detectability | High | 7 meta-tests, including the BUG-022 shape reconstructed |
| Security exposure | None directly | Protects the process that lost a security control |
| Performance | None | ~1s in `verify` |
| **Overall** | **LOW** | **Confidence HIGH.** No owner approval required |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Guard meta-suite | **68 passed** (up from 61) |
| Current repository | 19 carries: 6 disposed, 13 legitimately open |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
