---
sub_step_id: STEP-009.02
parent_step: STEP-009
title: Deterministic validators for dates, currency, units and coverage
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-001, REQ-AI-002]
blast_radius_id: TBD
depends_on: [STEP-009.01]
last_updated: 2026-09-04
---

# STEP-009.02 — Deterministic validators for dates, currency, units and coverage

## 1. Outcome
Everything that can be checked without a model is checked without a model.

## 2. Scope and boundary
**In scope:** Date, currency, unit and coverage validation; the deterministic layer the model's output must pass through.

**Not in this sub-step:** Extraction (`.04`); classification (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-001, REQ-AI-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material. This is the layer `ADR-002` requires to exist regardless of what the model does. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Dates validated in the destination zone using `domain.temporal`
- [ ] Currency validated as ISO 4217 with integer minor units (`domain.models.Money`)
- [ ] Units normalised deterministically — never by asking a model
- [ ] **Coverage checked before anything else**, so an out-of-coverage brief fails fast
- [ ] Validators are pure functions, fixture-tested, and run on model output as well as on typed input

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-001 | unit | Each validator rejects its seeded violation |
| — | unit | **Model output passes through the same validators as typed input** — no bypass path |
| — | unit | Dates validate across a DST boundary in the destination zone |
| — | unit | Money is integer minor units; a float is refused |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Validation failures are logged by class, not by content.

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
Revert the commit; extraction has no deterministic floor beneath it, so this must not be reverted alone once `.04` exists.

## 12. Acceptance criteria
- [ ] All four validator families implemented and pure
- [ ] Model output passes through the same path
- [ ] Coverage is checked first
- [ ] No float currency anywhere

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
| Notes / surprises | **`ADR-002` says deterministic engines own feasibility and the model owns language.** The way that erodes is not a decision — it is a code path where model output reaches state without passing the validators, added by someone in a hurry because the model's answer was already structured. The absence of a bypass is the thing to test, not the presence of the validators. |
