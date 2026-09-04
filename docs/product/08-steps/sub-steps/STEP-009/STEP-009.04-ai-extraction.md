---
sub_step_id: STEP-009.04
parent_step: STEP-009
title: Brief extraction through the AI gateway with structured output
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-001, REQ-AI-002]
blast_radius_id: TBD
depends_on: [STEP-009.03]
last_updated: 2026-09-04
---

# STEP-009.04 — Brief extraction through the AI gateway with structured output

## 1. Outcome
Prose becomes a structured proposal that the traveller confirms — and which cannot reach trip state unconfirmed.

## 2. Scope and boundary
**In scope:** `AI-001` extraction; the gateway boundary; structured output validation; the proposal shape.

**Not in this sub-step:** Classification (`.05`); confirmation (`.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-001, REQ-AI-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Extraction quality on real traveller prose. `.08` builds the evaluation set; until it exists, quality is unmeasured. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Extraction runs behind the AI gateway, never inline in a handler
- [ ] Output validated against `trip-brief-extraction.json` — **rejected, not repaired**, if it does not conform
- [ ] **Model output is a proposal**: it cannot mutate trip state without validation and explicit user authorisation (`ADR-002`, `REQ-AI-001`)
- [ ] Retrieved content and prompts are untrusted data, never instructions (`REQ-SEC-006`)
- [ ] Extraction failure falls back to `.03`'s editor, which is complete on its own

## 6. Contracts and schema changes
Consumes `trip-brief-extraction.json`. No change expected.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-001 | integration | **Model output cannot reach trip state without confirmation** — structural, on the absence of a write path |
| — | unit | Non-conforming output is rejected rather than coerced |
| — | security | Prompt-injection content in the input does not alter the extraction contract |
| — | integration | Extraction failure leaves the editor path fully usable |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Prompts and completions contain trip content and are not logged. Token counts and latency are.

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
Revert the commit; brief creation continues through `.03`. **This is the cleanest rollback in the step**, by design.

## 12. Acceptance criteria
- [ ] Extraction runs only behind the gateway
- [ ] Output is validated and rejected on non-conformance
- [ ] No unconfirmed path to trip state
- [ ] Failure degrades to the structured editor

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
| Notes / surprises | **The dangerous version of this feature is the helpful one.** An extraction that fills in a plausible date the traveller did not say produces a brief they will confirm without reading closely, and `REQ-CONS-004`'s zero-hard-constraint-violation promise is then resting on a guess somebody clicked past. `.05`'s inferred class exists for exactly this, and it only works if extraction refuses to present an inference as a statement. |
