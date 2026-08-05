---
sub_step_id: STEP-004.05
parent_step: STEP-004
title: AsyncAPI event contracts with delivery guarantees (EVT-001…008)
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-006, REQ-DATA-008]
blast_radius_id: BR-026
depends_on: [STEP-004.04]
last_updated: 2026-08-05
---

# STEP-004.05 — AsyncAPI event contracts with delivery guarantees (EVT-001…008)

## 1. Outcome
All eight domain events are specified with envelope, schema, partition key and an **explicit delivery guarantee** each.

## 2. Scope and boundary
**In scope:** `contracts/asyncapi.yaml`; shared envelope; per-event payload schemas; delivery and ordering semantics.

**Not in this sub-step:** Outbox implementation ([STEP-006](../../STEP-006-canonical-data-model-and-event-backbone.md)); consumer implementations.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-006, REQ-DATA-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | DEC-009 (queue vs Kafka) does not change the contract, only the transport — confirm that holds |
| Blast radius | BR-026 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Shared envelope: event_id, type, occurred_at, recorded_at, tenant_id, correlation_id, causation_id, actor, schema_version
- [ ] Eight event schemas with **IDs and classifications only — no trip content, evidence prose, personal data or location**
- [ ] Delivery guarantee declared per event (at-least-once vs. exactly-once effect)
- [ ] Partition key `trip_id` with per-trip ordering documented as the only guarantee
- [ ] `EVT-003` carries seed and model versions so reproducibility is auditable from the stream

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-006 | contract | Every event declares a delivery guarantee |
| — | contract | **No event schema permits personal data** |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-026` post-change section
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
- [ ] Eight events specified with envelope and guarantees
- [ ] Payload schemas structurally exclude personal data
- [ ] Ordering guarantees documented and scoped to per-trip

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Excluding personal data from event payloads at the schema level is what makes REQ-PRIV-006 deletion tractable — events fan out to stores with different retention. |
