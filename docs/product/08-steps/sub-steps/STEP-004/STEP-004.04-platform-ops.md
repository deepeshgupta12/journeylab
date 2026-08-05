---
sub_step_id: STEP-004.04
parent_step: STEP-004
title: Privacy, admin, coverage and job operations (API-015…018)
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005, REQ-PRIV-005]
blast_radius_id: BR-025
depends_on: [STEP-004.03]
last_updated: 2026-08-05
---

# STEP-004.04 — Privacy, admin, coverage and job operations (API-015…018)

## 1. Outcome
Platform surfaces — privacy requests, admin overrides, public coverage and job streaming — are specified with their distinctive auth and exposure rules.

## 2. Scope and boundary
**In scope:** `API-015` privacy requests, `API-016` evidence overrides, `API-017` public coverage, `API-018` SSE job events.

**Not in this sub-step:** Implementations; the knowledge-graph query API (internal, [STEP-026](../../STEP-026-knowledge-graph-platform.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005, REQ-PRIV-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-025 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] `API-015` export/correct/withdraw/delete with tracked status
- [ ] `API-016` override declaring **four-eyes approval** in its contract
- [ ] `API-017` coverage — **public, unauthenticated, and must not expose provider identities**
- [ ] `API-018` SSE with heartbeats so a slow job is distinguishable from a dead connection
- [ ] Cancellation contract for long-running jobs

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-005 | contract | Privacy request lifecycle fully specified |
| TST-EVID-006 | contract | Coverage response exposes no provider identity |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-025` post-change section
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
- [ ] Four operations specified
- [ ] Coverage endpoint leaks no provider identity or quota detail
- [ ] SSE contract includes heartbeats and cancellation
- [ ] Four-eyes declared in the override contract

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | SSE heartbeats are a product requirement in disguise: without them the UI cannot distinguish a 40-second solve from a dead connection, and REQ-NFR-003 forbids a silent spinner. |
