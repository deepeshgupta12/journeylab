---
sub_step_id: STEP-004.01
parent_step: STEP-004
title: Global API conventions: errors, pagination, idempotency, ETags
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005]
blast_radius_id: BR-022
depends_on: [STEP-003.08]
last_updated: 2026-08-05
---

# STEP-004.01 — Global API conventions: errors, pagination, idempotency, ETags

## 1. Outcome
One set of conventions governs every endpoint, so no service invents its own error shape, pagination or concurrency semantics.

## 2. Scope and boundary
**In scope:** RFC 9457 problem details with stable `type` URIs; cursor pagination; `Idempotency-Key`; ETag/`If-Match`; correlation headers; rate-limit declarations.

**Not in this sub-step:** Individual operations (`.02`–`.04`); implementations behind them.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Rate-limit values need capacity projections that do not exist yet (ASM-002) — declare the mechanism, defer the numbers |
| Blast radius | BR-022 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Problem-details schema with the error-code register from [ERROR_MODEL](../../../04-contracts/ERROR_MODEL.md)
- [ ] Cursor pagination envelope (offset pagination is not supported)
- [ ] `Idempotency-Key` required on all commands
- [ ] ETag and `If-Match` on mutable resources
- [ ] **403 and 404 share an identical body shape** to prevent enumeration
- [ ] Money as integer minor units; RFC 3339 timestamps with explicit IANA zone

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-005 | contract | Examples validate; problem details conform to RFC 9457 |
| — | contract | 403 and 404 bodies indistinguishable |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-022` post-change section
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
- [ ] Conventions documented in OpenAPI and enforced by schema
- [ ] Error codes match the register
- [ ] Idempotency and concurrency semantics declared per operation
- [ ] Enumeration prevented by identical 403/404 shapes

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Getting 403/404 indistinguishability into the shared convention is far cheaper than retrofitting it across 18 operations. |
