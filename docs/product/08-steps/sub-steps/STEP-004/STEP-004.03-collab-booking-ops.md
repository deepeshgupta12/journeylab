---
sub_step_id: STEP-004.03
parent_step: STEP-004
title: Collaboration, booking, live and feedback operations (API-010…014)
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005]
blast_radius_id: BR-030
depends_on: [STEP-004.02]
last_updated: 2026-08-11
---

# STEP-004.03 — Collaboration, booking, live and feedback operations (API-010…014)

## 1. Outcome
Phase 2–3 surfaces are contract-specified now so later steps implement against a stable shape rather than inventing one.

## 2. Scope and boundary
**In scope:** `API-010` invitations, `API-011` booking handoff, `API-012` activation, `API-013` repairs, `API-014` feedback.

**Not in this sub-step:** Implementations (Phase 2–3 steps).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **NOT BLOCKED** for impact; `gitnexus_query` still unusable (`BR-029` §3) |
| HEAD / indexed commit | `dd01499` / `dd01499` — matched |
| Queries run | `impact(safe_detail)` → 2 impacted, 1 process, `epistemic: exact`; `impact(ERROR_CODES)` → **ambiguous**, same declaration indexed twice (`BR-030` §3); `detect_changes()` |
| Unknown / low-confidence areas | Offline manifest shape depends on STEP-017 device constraints — **schema left extensible**, typed entries plus room to grow. **New:** the register lists `collaboration.invitation_expired` at 403 while `REQ-SEC-008` says "leak nothing"; no operation returns it yet, so it is flagged for `.04` rather than changed (`BR-030` §6.2) |
| Blast radius | **[BR-030](../../../10-logs/blast-radius/BR-030-collab-booking-live-feedback.md) — MEDIUM, confidence HIGH.** The record predicted `BR-024`; that number was taken by STEP-003.07 |
| Approval required? | **No** |

## 5. Implementation plan
- [x] `API-010` invitations — required expiry with no default, `trip_owner` excluded from the role enum, token returned **once**, immediate irreversible revocation
- [x] `API-011` handoff — **no payment field exists anywhere in the contract**, asserted by scanning every property name against 21 payment-shaped names, with a meta-test proving the scan works
- [x] `API-012` activation — offline manifest left **extensible**, because freezing a guess at device constraints would make the correction breaking
- [x] `API-013` repair generation separate from acceptance — enforced by **shape**: generation takes no `If-Match`, acceptance does
- [x] `API-014` feedback — `consent_scope` required, narrowest option first, and **no field can record the absence of feedback**
- [x] Estimated vs. confirmed as distinct states — a three-value enum, with the boolean spellings forbidden by test

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-BOOK-002 | contract | No schema permits a payment credential | ✅ whole-document scan, **plus a meta-test that the scan can find one** |
| TST-LIVE-005 | contract | Repair generation and acceptance are distinct | ✅ and their `If-Match` signatures differ, so the separation is structural |
| — | contract | Estimated/confirmed are states; no boolean flag exists | ✅ |
| — | contract | Invitations expire, cannot confer ownership, token unreadable after issue | ✅ |
| — | contract | Feedback requires consent; absence cannot be recorded | ✅ |
| — | contract | Phase 3 operations still obey the shared conventions | ✅ re-asserted across **all 16** |

29 assertions. Python suite: 440 → **469**.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-024` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 469 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Purely additive |
| R3 graph diff as expected | **PASS** | Contract and tests only |
| R4 untested requirements | **PASS — improved** | REQ-BOOK-004, REQ-SEC-008, REQ-CONS-011, REQ-PRIV-003 |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | No operation accepts a tenant parameter |

**Overall:** **PASS**. Detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Five operations specified — seven declared, because revoke and accept each needed to be their own operation
- [x] Payment credentials structurally impossible — **there is nowhere to put one**, asserted by scanning every property name in the document, with a meta-test proving the scan can find a seeded field
- [x] Repair generation cannot mutate canonical state — separated by signature, not by convention: generation takes no `If-Match`, acceptance does
- [x] Estimated/confirmed distinction is structural — a three-value enum, with `is_confirmed` and its variants forbidden by test

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. Two stale assertions from earlier sub-steps corrected — see the regression entry |
| Notes / surprises | The prediction was right and needed one addition: *"making payment credentials unrepresentable in the schema is stronger than validating them away — there is nothing to forget to validate."* True, but only if the unrepresentability is **checked**, and a test that searches for something absent passes identically when the search is broken. So the scan has a meta-test that seeds `card_number` into a synthetic document and requires the same walk to find it.<br><br>**Separating repair generation from acceptance turned out to be a shape, not a rule.** Generation takes no `If-Match` and acceptance does. Requiring a version precondition on a read-only projection would imply it mutates, and the next person to touch it would make that true — the signature is what keeps the two apart when the comment is skimmed.<br><br>**A conflict I recorded rather than resolved.** The register lists `collaboration.invitation_expired` at 403 while `REQ-SEC-008` says "leak nothing"; distinguishing "expired" from "never existed" tells a token-guessing attacker which guesses are real. No operation returns it yet — redemption is not declared — so nothing is wrong today. Changing a security-relevant status with no operation to test it against would be a change nothing exercises, so it is flagged for `.04`.<br><br>Two stale assertions in two consecutive sub-steps, both mine: `paths == {}` in `.02` and an exhaustive operation set in `.03`. Both were correct when written and became wrong as the surface grew. The pattern is asserting the current *extent* of something designed to extend. |
