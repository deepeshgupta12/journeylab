---
sub_step_id: STEP-005.10
parent_step: STEP-005
title: Provider health events and coverage wiring
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-006, REQ-TRIP-002]
blast_radius_id: BR-039
depends_on: [STEP-005.09]
last_updated: 2026-08-05
---

# STEP-005.10 — Provider health events and coverage wiring

## 1. Outcome
Provider degradation surfaces as `EVT-008`, drives the public coverage model, and causes new trips in affected regions to be **refused rather than partially simulated**.

## 2. Scope and boundary
**In scope:** Health state machine; `EVT-008` emission; coverage model updates; admin surface wiring.

**Not in this sub-step:** Coverage UI ([STEP-007](../../STEP-007-discovery-landing-and-destination-coverage.md)); admin console ([STEP-021](../../STEP-021-administration-and-curation-console.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-006, REQ-TRIP-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-039 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Health state machine: healthy → degraded → circuit-open → recovering
- [ ] `EVT-008` emitted on every transition
- [ ] Coverage model consumes health and marks regions degraded
- [ ] **Region degradation refuses new trips** for affected coverage
- [ ] Health surfaced without exposing provider identity publicly

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-006 | resilience | Degradation is disclosed, not masked by cache |
| TST-TRIP-002 | e2e | Degraded region refuses new trips, produces no partial simulation |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-039` post-change section
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
- [ ] Health transitions emit `EVT-008`
- [ ] Coverage reflects degradation promptly
- [ ] Degraded regions refuse new trips
- [ ] Provider identity never public

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Refusing rather than partially simulating is the honesty commitment made concrete — and it is easier to enforce here, at the source, than in the UI. |
