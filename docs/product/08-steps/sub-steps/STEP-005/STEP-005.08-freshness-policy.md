---
sub_step_id: STEP-005.08
parent_step: STEP-005
title: Field-specific freshness policy and expiry
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-005, REQ-EVID-005]
blast_radius_id: BR-037
depends_on: [STEP-005.07]
last_updated: 2026-08-05
---

# STEP-005.08 — Field-specific freshness policy and expiry

## 1. Outcome
Each field class carries its own expiry, so closures expire in minutes while descriptions expire in weeks, and staleness is computed at time of use.

## 2. Scope and boundary
**In scope:** `services/ingestion/src/freshness.py`; field-class registry; age-at-use computation; staleness marking.

**Not in this sub-step:** Evidence-pack assembly ([STEP-010](../../STEP-010-destination-evidence-assembly.md)); UI display of staleness.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-005, REQ-EVID-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Threshold values per class need product sign-off (DEC-005) |
| Blast radius | BR-037 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Field-class registry: closures/disruptions (minutes), hours (fast), prices (medium), descriptions (slow)
- [ ] **Age-at-use** computed against observed time, not ingestion time
- [ ] **Effective-window check separate from freshness** — a freshly observed fact can still be inapplicable to the trip dates
- [ ] Staleness marking that travels with the fact
- [ ] Critical-field staleness blocks the affected option rather than degrading silently

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-005 | unit | Each field class expires per its own threshold |
| TST-EVID-005 | integration | Stale critical fact blocks the option; stale non-critical lowers confidence |
| — | unit | Fresh observation with a non-covering effective window is treated as a coverage gap |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-037` post-change section
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
- [ ] Field classes registered with distinct thresholds
- [ ] Age-at-use computed from observed time
- [ ] Effective-window and freshness treated as independent checks
- [ ] Critical staleness blocks rather than degrades

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Conflating freshness with applicability is the subtlest bug in this product: a fact fetched five minutes ago describing last summer's hours is fresh and wrong. |
