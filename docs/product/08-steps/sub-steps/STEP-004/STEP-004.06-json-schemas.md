---
sub_step_id: STEP-004.06
parent_step: STEP-004
title: Shared JSON Schemas including model-output schemas
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005, REQ-AI-002]
blast_radius_id: BR-027
depends_on: [STEP-004.05]
last_updated: 2026-08-05
---

# STEP-004.06 — Shared JSON Schemas including model-output schemas

## 1. Outcome
Request, response, event and **model-output** shapes share one schema library, so the deterministic boundary around AI output is contractual.

## 2. Scope and boundary
**In scope:** `contracts/jsonschema/`; shared types (money, temporal validity, provenance, constraint classes); model-output schemas for `AI-001`.

**Not in this sub-step:** Prompt content ([STEP-009](../../STEP-009-trip-brief-and-structured-constraints.md)); retrieval configuration.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005, REQ-AI-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-027 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Shared `Money` (integer minor units), `TemporalValidity` (observed/effective/recorded), `Provenance` (source, confidence, access label)
- [ ] `ConstraintClass` enum with the four values kept distinct
- [ ] **Model-output schema for TripBrief extraction** with per-field class and confidence
- [ ] Schema `$id` versioning
- [ ] Reuse enforced — no duplicate inline definitions

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-002 | contract | Model output violating the schema is rejected |
| — | CI | No duplicated inline type where a shared schema exists |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-027` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Shared types defined once and reused
- [ ] Model-output schemas exist and are versioned
- [ ] Schema violation is a hard rejection, not a coercion

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Defining the model-output schema as a contract artifact — not prompt text — is what makes 'fail closed' testable in CI rather than a runtime hope. |
