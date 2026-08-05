---
sub_step_id: STEP-005.04
parent_step: STEP-005
title: Transit routes, schedules and service alerts adapter
status: NOT_STARTED
owners: []
requirement_ids: [REQ-DATA-002, REQ-NFR-011]
blast_radius_id: BR-033
depends_on: [STEP-005.03]
last_updated: 2026-08-05
---

# STEP-005.04 — Transit routes, schedules and service alerts adapter

## 1. Outcome
Transit routes, schedules and service alerts are ingested with correct time-zone normalization and minute-level alert freshness.

## 2. Scope and boundary
**In scope:** `services/integrations/src/transit/`; GTFS-style feed handling; service calendars; alert stream; feed version pinning.

**Not in this sub-step:** Travel-matrix computation (`.05`); live impact matching ([STEP-018](../../STEP-018-condition-monitoring.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-NFR-011 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Alert feed latency is provider-specific and unknown until EXT-003 is selected |
| Blast radius | BR-033 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Feed ingestion with **pinned feed version**
- [ ] Service calendar handling including exceptions
- [ ] Stop coordinates resolved — an unresolvable stop is a coverage gap, not a guess
- [ ] **Time-zone normalization** across the feed
- [ ] Service alerts with validity windows and minute-level freshness
- [ ] Degradation: no transit ⇒ walking/driving only, gap disclosed

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-002 | integration | Feed version pinned; drift rejected |
| TST-NFR-011 | integration | Alert freshness meets the documented SLO |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-033` post-change section
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
- [ ] Feed version pinned and drift detected
- [ ] Service calendars correct including exceptions
- [ ] Unresolvable stops become coverage gaps
- [ ] Transit unavailability disclosed rather than silently substituted

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Service-calendar exceptions (holidays, engineering works) are where naive GTFS handling produces itineraries that fail on the day. |
