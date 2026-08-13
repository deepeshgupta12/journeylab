---
sub_step_id: STEP-004.09
parent_step: STEP-004
title: Detect documented semantic change in the contract
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-008]
blast_radius_id: BR-040
depends_on: [STEP-004.08]
last_updated: 2026-08-13

# ENH-001, accepted by the repository owner 2026-08-13.
---

# STEP-004.09 — Detect documented semantic change in the contract

> **Why this exists.** `ENH-001`, accepted against my own recommendation to defer
> — which is the owner's call. `CONTRACT_CHANGE_POLICY` §1: *"Changing what a field
> means while keeping its name and type passes every automated compatibility check
> and breaks every consumer. It is always treated as breaking."* The `.08`
> classifier is structural and says so in its own docstring. This is the category
> with **no automated coverage at all**, and it is the one the policy calls most
> dangerous. Moves STEP-004 from `VERIFIED` 8/8 to 9/9.

## 1. Outcome
A field whose meaning changed while its shape did not is **reported**, wherever the
author documented the new meaning.

## 2. Scope and boundary
**In scope:** description comparison between `contracts/` and
`contracts/baseline/`; normalisation that removes formatting noise; a
`REVIEW_REQUIRED` report; wiring into the release checklist, where it is consumed.

**Not in this sub-step:** failing the build. See §6 — that is a deliberate design
decision, not an omission.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-008 | A documented meaning change is surfaced before release | §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `776e385` — matched HEAD at pre-change |
| Queries run | `impact(diff_contracts, upstream)`; measured the real false-positive rate against the live corpus before choosing normalisation (§6) |
| Unknown / low-confidence areas | **An undocumented semantic change stays invisible.** That is not solvable and is stated rather than implied |
| Blast radius | **[BR-040](../../../10-logs/blast-radius/BR-040-semantic-change.md)** |
| Approval required? | Per blast-radius score |

## 5. Implementation plan
- [x] Walks every described property in both documents — 54 of them
- [x] Normalises away reflow, emphasis, code marks **and sentence case** — one test each, all asserting no report
- [x] Reports with **both** texts, so a reviewer decides in one glance
- [x] Does **not** fail the build (§6); the PASS line names outstanding reviews so a structural pass never reads as a semantic one
- [x] Wired into `RELEASE_READINESS_CHECKLIST` §2 and pointed at from `CONTRACT_CHANGE_POLICY` §1
- [x] **Measured: 0 findings across 54 properties** — and the measurement is a test, so the normaliser degrades loudly

## 6. Two decisions the enhancement's own risk section forces

`ENH-001` was explicit: *"If the false-positive rate is not driven near zero first,
this should not ship."* Both decisions below exist to honour that.

### It reports; it does not fail the build

A check that fails on a typo fix is one people learn to bypass, and this repository
already has one degraded signal that reads like a real answer (`gitnexus_query`,
`BR-029` §3). The lesson recorded there was that **a check nobody can trust is
worse than a check nobody has.**

So the exit code is unchanged and the finding is printed. The cost is that a report
nobody reads is worthless — which is why it is wired into the **release checklist**
rather than left in build output. It is consumed at the moment it matters: the
point where a semantic change stops being free.

### Normalisation is chosen from measurement, not taste

Three classes of edit change a description's bytes without changing its meaning:

| Noise | Example | Why it is safe to ignore |
| --- | --- | --- |
| **Reflow** | a YAML block scalar rewrapped at 80 columns | The rendered text is identical |
| **Emphasis** | `must` → `**must**` | Markdown decoration |
| **Code marks** | `Money` → `` `Money` `` | Same |

Whitespace collapse plus emphasis stripping removes all three. What remains is a
genuine wording change — including a typo fix, which **will** fire and is accepted:
the report shows both texts, so a reviewer dismisses it in one glance, and
descriptions change rarely enough that the volume is near zero.

**The measured rate on the real corpus is recorded in §13**, because "near zero"
asserted is worth nothing next to "near zero" counted.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-008b | Unit | A changed description on a structurally identical property is reported |
| — | Unit | Reflow alone is **not** reported |
| — | Unit | Emphasis and backtick changes alone are **not** reported |
| — | Unit | A property that changed structurally is **not** double-reported here |
| — | Unit | A new or removed property is not a semantic change |
| — | Guard meta | The report does not change the gate's exit code |

## 8. Telemetry, security and accessibility
None — a build-time report over two documents.

## 9. Documentation to update
- [x] Sub-step completion record
- [x] IMPLEMENTATION_LOG `IMPL-037` · REGRESSION_LOG · ENHANCEMENT_LOG (`ENH-001` **DELIVERED**)
- [x] `BR-040`
- [x] Parent §21 · MASTER_TRACKER · `RELEASE_READINESS_CHECKLIST` §2 · `CONTRACT_CHANGE_POLICY` §1

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 736 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS — and now partly semantic** | Structural verdict unchanged; the semantic report does not alter the exit code |
| R3 graph diff as expected | **PASS** | One function, one call site, one test class, three documents |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-008's semantic clause gains its first coverage |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…025; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert the commit. The gate returns to structural-only, which is `.08`'s state.

## 12. Acceptance criteria
- [x] A documented meaning change is reported with both texts — seeded on the real contract
- [x] Reflow, emphasis, code marks and sentence case produce **no** report
- [x] The gate's exit code is unchanged
- [x] **Measured: 0 of 54.** Recorded in §13 and enforced by a test
- [x] Consumed by `RELEASE_READINESS_CHECKLIST` §2, not merely printed

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-13 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Measured false-positive rate | **0 findings across 54 described properties** |
| Bugs found | None. One of my own, caught immediately: a compiled regex with no `re` import |
| Notes / surprises | **I recommended deferring this and was overridden, and the override was reasonable.** My argument was cost-of-false-positives, not that the gap was acceptable — `CONTRACT_CHANGE_POLICY` §1 calls this the most dangerous category and it had no automated coverage at all. The override turned my objection into the acceptance criterion: measure the rate. Zero of fifty-four.<br><br>**The insight fits in a sentence.** A semantic change is undetectable in general; a *documented* one is not. An author who redefines a field and updates its description leaves a machine-readable trace. This follows that trace and nothing else — "invisible" becomes "invisible only when undocumented", which is smaller and not closed. An undocumented redefinition stays invisible and no tool fixes that.<br><br>**Reporting rather than failing is the whole design, not a compromise.** A check that fails on a reworded sentence gets bypassed, and `BR-029` §3 records what an untrustworthy signal costs here. But a report nobody reads is worth as little, so it is wired into the release checklist — the point where a semantic change stops being free — rather than left in build output.<br><br>**The measurement is a test.** If normalisation ever stops removing formatting noise, the suite fails rather than the check quietly becoming noise. And a companion test seeds a genuine redefinition and requires it to be caught, because a detector that found nothing would satisfy the first test perfectly while detecting nothing at all. |
