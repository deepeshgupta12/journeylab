---
sub_step_id: STEP-001.08
parent_step: STEP-001
title: A carried commitment cannot be dropped silently
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-KG-008, REQ-PLAT-002]
blast_radius_id: BR-039
depends_on: [STEP-001.07]
last_updated: 2026-08-13

# ENH-002, accepted by the repository owner 2026-08-13.
---

# STEP-001.08 — A carried commitment cannot be dropped silently

> **Why this exists.** `BUG-022`. `STEP-002.05` deferred server-side session
> revocation and wrote *"carried to STEP-002.07"*; `.07` closed `VERIFIED` listing <!-- carry-exempt: quotes BUG-022, does not make a carry -->
> four carried gaps, none of them that one. Nothing failed, because **a carry is
> prose** — `substep-docs.sh` checks that a `VERIFIED` sub-step has its three
> records, not that a promise made in one record was kept in another. The control
> everyone believed existed did not, for six sub-steps.

## 1. Outcome
A commitment deferred to a later sub-step cannot reach that sub-step's closure
without an explicit disposition. Forgetting is a build failure.

## 2. Scope and boundary
**In scope:** `tests/guards/carried-commitments.sh`; a disposition convention;
annotating every existing carry whose target has already closed.

**Not in this sub-step:** carries pointing at open steps — they are working as
intended and are the normal case.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-KG-008 | A deferral cannot outlive its target's closure unrecorded | §7 |
| REQ-PLAT-002 | The check runs locally in `pnpm verify`, not only in review | §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `34588be` — matched HEAD at pre-change |
| Queries run | A read-only prototype over all 51 sub-step records and every log before designing — the results changed the design twice (§6) |
| Unknown / low-confidence areas | The guard reads prose. It can prove a carry was **considered**; it cannot prove the underlying work was **done**. Stated in §6 rather than implied |
| Blast radius | **[BR-039](../../../10-logs/blast-radius/BR-039-carried-commitments.md)** |
| Approval required? | Per blast-radius score |

## 5. Implementation plan
- [x] Parses every document — 208 of them; most carries live in logs and blast radii, not sub-step records
- [x] Resolves the relative `carried to .07` form against the containing sub-step <!-- carry-exempt: describes the syntax -->
- [x] Excludes `STEP-NNN` placeholders, `09-templates/`, and prose marked `carry-exempt`
- [x] **Fails when a carry names an already-`VERIFIED` target and has no disposition**
- [x] Six existing carries annotated — **one of which turned out to be live** (§6)
- [x] 7 meta-tests: the BUG-022 shape reconstructed and killed; disposed, withdrawn, open and placeholder cases all pass

## 6. Two design decisions the prototype forced

A read-only prototype ran before any of this was built, and it was wrong twice.

### The first heuristic was "the target must mention the source". It does not survive contact.

`STEP-004.01` carried the `auth/errors.py` RFC 9457 migration to `STEP-004.04`.
`.04` **did** deal with it — by establishing that the carry was mistaken: *"I said
in a hand-off that `auth/errors.py` migrates to RFC 9457 here… Neither is true:
STEP-004 declares contracts only."*

That is a legitimate discharge and it never names `STEP-004.01`. Discharge has at
least three honest shapes:

| Shape | Example |
| --- | --- |
| **Done** | the work landed in the target |
| **Withdrawn** | the carry was mistaken (`STEP-004.04`) |
| **Re-routed** | it moved to a different target (`STEP-002.08`) |

None reliably mentions the source, so a mention-based check would fail two of the
three and train people to game it.

### The prototype flagged carries I had already fixed

`.04` and `.05` were reported as dropped — because `STEP-002.08` rewrote those
lines to **quote** the old carry while explaining the fix. The guard cannot tell a
live promise from a historical quotation of one.

That is exactly the false-positive class `ENH-002` predicted, and a check that
fires on already-fixed work is a check people learn to ignore.

### So: the disposition lives on the carry line

A carry is open until its own line says otherwise:

```
carried to STEP-NNN.MM                                 <- open, must be resolved
carried to STEP-NNN.MM — discharged at STEP-NNN.MM     <- the work was done
carried to STEP-NNN.MM — withdrawn: <reason>           <- the carry was mistaken
carried to STEP-NNN.MM — superseded by <what>          <- it moved, and this says where
```

(The example uses the `STEP-NNN.MM` placeholder deliberately: the guard already
skips it, so a document explaining the convention cannot fail on its own example.
Working that out was the third false positive this guard produced against its own
documentation.)

The guard fails only when a carry names an **already-`VERIFIED`** target and
carries no disposition. Re-routing is visible rather than free, which was
`ENH-002`'s stated risk: *"the cheapest way to satisfy the guard is to restate the
carry with a new destination"* — now that restatement is written down and
countable.

### What this cannot do

It proves a carry was **considered at closure**, not that the work was **done**.
Somebody can write `— withdrawn` dishonestly. That is the same limit as
`contracts/baseline/BASELINE.md` §3: the check converts silence into a specific,
recorded, reviewable claim. It does not make the claim true.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-KG-008b | Guard meta | A carry to a `VERIFIED` target with no disposition **fails** |
| — | Guard meta | The same carry with `— discharged at X` passes |
| — | Guard meta | A carry to an open step passes untouched |
| — | Guard meta | `STEP-NNN.MM` in a template is not treated as a carry |
| — | Guard meta | **The BUG-022 case, reconstructed, fails** |

## 8. Telemetry, security and accessibility
None — a documentation guard with no runtime surface.

## 9. Documentation to update
- [x] Sub-step completion record
- [x] IMPLEMENTATION_LOG `IMPL-036` · REGRESSION_LOG · ENHANCEMENT_LOG (`ENH-002` **DELIVERED**)
- [x] `BR-039`
- [x] Parent §21 · MASTER_TRACKER · README · `WAYS_OF_WORKING` (the convention, plus `ADR-017`)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 727 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One tool, one guard, six annotations, two documents |
| R4 untested requirements | **PASS — improved** | REQ-KG-008 gains an automated check where it had only a protocol |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…024; meta-suite **68/68** |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert the commit. The annotations are harmless prose; only the guard goes.

## 12. Acceptance criteria
- [x] A carry to a closed target without a disposition fails the build
- [x] The BUG-022 case, reconstructed, is caught — and names the target
- [x] No false positive on the current repository — 19 carries, 6 disposed, 13 open
- [x] The convention is in `WAYS_OF_WORKING`, where a contributor meets it

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-13 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None new. **One live commitment with no owner** — see below |
| Notes / surprises | **The throwaway prototype was worth more than the guard.** Running a read-only detector against the real corpus before designing killed two rules that would each have shipped and each been wrong. "The target must mention the source" fails two of the three honest discharge shapes — `STEP-004.04` discharged its carry by establishing the carry was *mistaken*, never naming the source. And it flagged carries I had already fixed, because `STEP-002.08` rewrote those lines to *quote* the old carry; a live promise and a historical quotation of one are textually identical.<br><br>**It found a commitment with no home on its first real run.** `auth/errors.py` still returns the STEP-002.02 shape, not RFC 9457. `STEP-004.01` carried the migration to `.04`; `.04` correctly established it was not its job — and nobody re-carried it. Two error shapes have coexisted since STEP-004.01 with the record pointing at a sub-step that had declined the work. `BR-028` §7 disclosed the shapes openly at the time, so nothing was hidden; what was lost was **ownership**, which is exactly what `BUG-022` was. Re-carried to `STEP-008`.<br><br>**The guard failed on its own documentation five times** — placeholders, a quoted carry, a literal `.07` example, the fenced syntax block, and finally the enhancement-log entry recording all of them. Each was fixed by a decision rather than a loosened rule, because the risk `ENH-002` costed was exactly that false positives teach people to click through.<br><br>**The limit is stated, not implied.** It proves a carry was *considered* at closure, not that the work was *done*: `— withdrawn: nonsense` passes. Same honest limit as `BASELINE.md` §3. |
