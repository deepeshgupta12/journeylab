---
sub_step_id: STEP-005.06
parent_step: STEP-005
title: Affiliate deep-link generation and signed callback receipt
status: NOT_STARTED
owners: []
requirement_ids: [REQ-BOOK-001, REQ-BOOK-002]
blast_radius_id: BR-035
depends_on: [STEP-005.05]
last_updated: 2026-08-05
---

# STEP-005.06 — Affiliate deep-link generation and signed callback receipt

## 1. Outcome
Deep links preserve itinerary context where the provider permits, and attribution callbacks are verified before parsing — with **no payment credential anywhere**.

## 2. Scope and boundary
**In scope:** `services/integrations/src/affiliate/`; link generation; signed webhook receipt; replay-window enforcement; attribution records.

**Not in this sub-step:** Booking UI and reconciliation into itinerary items ([STEP-016](../../STEP-016-booking-handoff.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-BOOK-001, REQ-BOOK-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | **No partner selected (EXT-005).** Parameter-preservation behaviour is the core ASM-012 unknown |
| Blast radius | BR-035 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Deep-link generation with dates, party size and product identifiers where permitted
- [ ] **Record which parameters each partner actually preserves** — this validates ASM-012 empirically
- [ ] **Verify webhook signature before parsing the body**
- [ ] Enforce replay window; accept duplicates idempotently
- [ ] Enqueue for async processing — no business work in the webhook request
- [ ] Attribution record with no payment data

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-BOOK-002 | security | No code path can persist a payment credential |
| — | security | Unsigned webhook discarded; replayed webhook outside window rejected |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-035` post-change section
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
- [ ] Links preserve parameters per partner capability
- [ ] Signature verified before parsing
- [ ] Replay window enforced, duplicates idempotent
- [ ] No payment credential representable

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Verifying the signature before parsing matters: parsing attacker-controlled JSON first is itself the attack surface. |
