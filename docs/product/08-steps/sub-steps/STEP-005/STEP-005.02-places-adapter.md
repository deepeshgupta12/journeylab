---
sub_step_id: STEP-005.02
parent_step: STEP-005
title: Places, hours and accessibility provider adapter
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-001, REQ-DATA-005]
blast_radius_id: BR-031
depends_on: [STEP-005.01]
last_updated: 2026-08-05
---

# STEP-005.02 — Places, hours and accessibility provider adapter

## 1. Outcome
Place entities, opening hours, closures, accessibility attributes and price ranges are ingested with full provenance and field-specific freshness.

## 2. Scope and boundary
**In scope:** `services/integrations/src/places/`; sanitized fixtures; licence record; hours parsing into intervals with time zones.

**Not in this sub-step:** Entity resolution (`.07`); freshness policy definition (`.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-001, REQ-DATA-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | **No provider selected (EXT-001).** Build against fixtures; real-payload assumptions are unverified |
| Blast radius | BR-031 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] **Licence record captured before any ingestion is enabled** (`REQ-DATA-001`)
- [ ] Adapter mapping provider payload to canonical place fields
- [ ] **Hours parsed into intervals with an explicit IANA time zone** — never naive local times
- [ ] Accessibility attributes captured **as declared**, never inferred
- [ ] Sanitized fixtures for success, empty, error, quota and schema-change cases
- [ ] Provenance stamped: source, observed_at, effective window, confidence

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-001 | CI | Ingestion refused without a licence record |
| TST-DATA-005 | unit | Seasonal hours produce correct effective windows |
| — | unit | Hours spanning midnight and DST parse correctly |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-031` post-change section
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
- [ ] Licence record exists and gates ingestion
- [ ] Hours carry time zones and effective windows
- [ ] Accessibility attributes never inferred
- [ ] Fixtures cover all five cases

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | This adapter carries RISK-001 — no provider is identified. Everything here is buildable against fixtures, but cannot be validated until a contract exists. |
