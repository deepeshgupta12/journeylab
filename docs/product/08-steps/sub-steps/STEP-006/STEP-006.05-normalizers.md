---
sub_step_id: STEP-006.05
parent_step: STEP-006
title: Provider payload to canonical entity normalizers
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-007, REQ-DATA-004]
blast_radius_id: BR-044
depends_on: [STEP-006.04]
last_updated: 2026-08-05
---

# STEP-006.05 — Provider payload to canonical entity normalizers

## 1. Outcome
Validated provider payloads become canonical entities with full provenance, and anything that does not map cleanly is rejected rather than coerced.

## 2. Scope and boundary
**In scope:** `services/ingestion/src/normalizers/`; per-provider mapping; provenance stamping; rejection on unmappable input.

**Not in this sub-step:** Provider fetching ([STEP-005](../../STEP-005-source-integrations-and-ingestion.md)); entity resolution (`STEP-005.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-007, REQ-DATA-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-044 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Normalizer per provider payload type
- [ ] Provenance stamped: source, observed_at, effective window, confidence, licence label
- [ ] **Unmappable field rejects the record** — never a default or a guess
- [ ] Schema version recorded on every canonical record
- [ ] Normalizers are pure functions, independently testable against fixtures

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-007 | unit | Every canonical record carries full provenance |
| — | unit | Unmappable payload is rejected, not defaulted |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-044` post-change section
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
- [ ] Normalizers pure and fixture-tested
- [ ] Provenance complete on every record
- [ ] Unmappable input rejected with a reason
- [ ] Schema version recorded

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Defaulting a missing field is how a venue with unknown accessibility silently becomes 'accessible' in a plan. |
