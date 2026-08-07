---
sub_step_id: STEP-005.05
parent_step: STEP-005
title: Routing engine adapter with explicit profile declaration
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-A11Y-003]
blast_radius_id: BR-034
depends_on: [STEP-005.04]
last_updated: 2026-08-05
---

# STEP-005.05 — Routing engine adapter with explicit profile declaration

## 1. Outcome
Travel-time matrices are computed per mode and time window, and the provider **declares which profiles it genuinely supports** — including wheelchair.

## 2. Scope and boundary
**In scope:** `services/routing/src/matrix.py`; provider-independent profile interface; matrix caching keyed by mode, window and licence terms.

**Not in this sub-step:** Solver consumption ([STEP-012](../../STEP-012-scenario-optimisation-and-simulation.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-A11Y-003 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | **DEC-008 unresolved.** Wheelchair data quality unknown; propose a provider with rationale when this sub-step is reached |
| Blast radius | BR-034 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Provider-independent profile interface: walking, transit, driving, **wheelchair**
- [ ] **Explicit profile-support declaration** — silent fallback from wheelchair to walking is prohibited
- [ ] Time-dependent matrices (departure time affects duration)
- [ ] Cache keyed by mode × time window × **provider licence terms**
- [ ] **Straight-line distance is never substituted** for a routing failure
- [ ] Provenance: provider, timestamp, assumptions retained per result

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-003 | integration | Wheelchair profile unsupported ⇒ **explicit limitation**, not silent walking substitution |
| — | unit | Straight-line distance never appears in a matrix result |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-034` post-change section
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
- [ ] Four profiles behind one interface
- [ ] Profile support declared explicitly
- [ ] Time-dependent matrices correct
- [ ] Cache key includes licence terms
- [ ] No straight-line fallback anywhere

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Silent wheelchair-to-walking fallback would make an accessibility claim the data cannot support — a safety issue, not a feature gap (ASM-020). |
