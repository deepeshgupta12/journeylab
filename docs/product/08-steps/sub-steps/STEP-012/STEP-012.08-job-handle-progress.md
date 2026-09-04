---
sub_step_id: STEP-012.08
parent_step: STEP-012
title: Job handle, SSE progress and cancellation
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-NFR-004]
blast_radius_id: TBD
depends_on: [STEP-012.07]
last_updated: 2026-09-04
---

# STEP-012.08 — Job handle, SSE progress and cancellation

## 1. Outcome
Generation runs as a cancellable job with honest progress, and cancelling actually stops the work.

## 2. Scope and boundary
**In scope:** Job handle; SSE progress; cancellation; `JobEvent` emission.

**Not in this sub-step:** Degradation ordering (`.09`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-NFR-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Progress honesty. A solver's progress is not linear, and a bar that sits at 90% is worse than one that says what it is doing. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Job handle returned immediately; generation never blocks a request
- [ ] **`JobEvent.sequence` populated** — it is required, and `BUG-021` exists because it was optional while its description promised gap detection
- [ ] Progress states describe the phase, not a fabricated percentage
- [ ] **Cancellation stops the work**, not just the stream — a cancel that leaves the solver running is a lie
- [ ] Cancellation leaves no partial scenario

## 6. Contracts and schema changes
Emits `JobEvent` as declared. `sequence` and `model_versions` are required — `BUG-021`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-NFR-004 | integration | A cancel stops the solver, verified by resource release |
| — | integration | `JobEvent.sequence` has no gaps across a run |
| — | integration | **Cancellation leaves no partial scenario** |
| — | browser | Progress is announced to assistive technology |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Job duration, cancellation rate, phase timings.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit; generation blocks the request path and cannot be cancelled.

## 12. Acceptance criteria
- [ ] Non-blocking job handle
- [ ] Sequence gap-free
- [ ] Cancellation stops the work
- [ ] No partial scenario on cancel

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Mutation testing | — |
| Bugs found | — |
| Notes / surprises | **A cancel button that closes the stream while the solver keeps running is the version everybody ships first** — the UI responds instantly, the user is satisfied, and the cluster is doing work nobody wants. `BUG-021` is the precedent worth remembering: `sequence` was optional while its own description promised gap detection, which is the same shape of promise unbacked by mechanism. |
