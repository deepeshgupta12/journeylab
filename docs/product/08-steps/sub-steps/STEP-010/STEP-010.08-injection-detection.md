---
sub_step_id: STEP-010.08
parent_step: STEP-010
title: Injection detection on retrieved content
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-006, REQ-AI-009]
blast_radius_id: TBD
depends_on: [STEP-010.07]
last_updated: 2026-09-04
---

# STEP-010.08 — Injection detection on retrieved content

## 1. Outcome
Retrieved content is treated as data, and content attempting to act as instruction is detected and neutralised.

## 2. Scope and boundary
**In scope:** Injection detection on retrieved text; the untrusted-data boundary; neutralisation.

**Not in this sub-step:** Prompt construction (`STEP-013.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-SEC-006, REQ-AI-009 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Detection coverage. Injection is adversarial and a detector is never complete — the honest position is defence in depth, not a claim of completeness. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] **Retrieved content and tool descriptions are untrusted data, never instructions** (`REQ-SEC-006`)
- [ ] Structural separation between instruction and data in every prompt, not a delimiter convention
- [ ] Detection on retrieved spans, with detections recorded rather than silently dropped
- [ ] A detected span is neutralised and the fact is marked, not discarded — dropping it hides the attack
- [ ] The detector has a seeded-violation control it must catch

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-SEC-006 | security | Injected instructions in retrieved content do not alter behaviour |
| — | security | **The detector catches its seeded violation** — a clean run from a broken detector proves nothing |
| — | integration | A detected span is marked, not silently dropped |
| — | adversarial | A corpus of known injection patterns |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Detections are security events with the span hashed, not stored.

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
Revert the commit. **Retrieved content then reaches prompts unchecked** — an emergency-only rollback.

## 12. Acceptance criteria
- [ ] Instruction and data are structurally separated
- [ ] Detections are recorded, not dropped
- [ ] The detector has a working negative control
- [ ] An adversarial corpus exists

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
| Notes / surprises | **A detector asserted only to pass is indistinguishable from `return True`** — STEP-006.09 proved that with a purity checker that survived being replaced by a constant. For a security detector the same gap is worse: the green run becomes the evidence that no attack occurred. The seeded-violation control is not optional here. |
