---
sub_step_id: STEP-004.04
parent_step: STEP-004
title: Privacy, admin, coverage and job operations (API-015…018)
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005, REQ-PRIV-005]
blast_radius_id: BR-031
depends_on: [STEP-004.03]
last_updated: 2026-08-11
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
| Graph status | ✅ up to date — but see the next row |
| HEAD / indexed commit | `6ea8436` / `6ea8436` — matched |
| Queries run | `impact(CLIENT_VISIBLE)` → ambiguous, then `0 impacted` / `epistemic: exact` **which is wrong**; `detect_changes()` |
| Unknown / low-confidence areas | **The tool gave a confidently wrong answer.** `CLIENT_VISIBLE` has five references across two files and the graph reported none, labelled `exact`. Sixth limitation recorded across BR-024…031; a `0 impacted` result is trustworthy only for a Python function (`BR-031` §3) |
| Blast radius | **[BR-031](../../../10-logs/blast-radius/BR-031-platform-operations.md) — MEDIUM, confidence HIGH** in the change, reduced in the tooling. The record predicted `BR-025`; taken by STEP-003.08 |
| Approval required? | **No** |

## 5. Implementation plan
- [x] `API-015` export/correct/withdraw/delete — tracked **per store**, all seven `REQ-PRIV-006` names, with `partially_failed` as a distinct state because six of seven is not complete
- [x] `API-016` override declaring four-eyes — `status` is **absent from the closed request schema**, so a caller cannot ask for `active` and skip approval
- [x] `API-017` coverage — the **only** operation declaring `security: []`, and a test counts them. `provider_health` is one aggregate enum; the schema is closed; eight leak-shaped names are asserted absent
- [x] `API-018` SSE with heartbeats — plus warnings and monotonic sequencing, so a reconnecting client knows whether it missed anything
- [x] Cancellation — `202`, not `204`: a job stops at a safe point and `REQ-NFR-004` requires the last valid state to survive

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-PRIV-005 | contract | Lifecycle fully specified — four kinds, trackable, seven stores, partial failure distinct | ✅ |
| TST-EVID-006 | contract | No provider identity or quota detail in the public response | ✅ eight names asserted absent |
| — | contract | **Exactly one** unauthenticated operation exists | ✅ counted, not assumed |
| — | contract | The server sets override status, not the caller | ✅ |
| — | contract | Heartbeat, warning and sequence are declared event types | ✅ |

23 assertions. Python suite: 469 → **492**.

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
| R1 full regression suite | **PASS** | 492 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Purely additive |
| R3 graph diff as expected | **PASS, with a caveat** | See §4 — the graph reported a false zero |
| R4 untested requirements | **PASS — improved** | REQ-PRIV-006/007, REQ-EVID-006 |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Coverage is tenant-free by construction |

**Overall:** **PASS**. Detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Four operations specified — six declared, because tracking a privacy request and cancelling a job each needed to be their own operation
- [x] Coverage leaks no provider identity or quota detail — a closed schema, one aggregate health enum, and eight leak-shaped names asserted absent
- [x] SSE includes heartbeats and cancellation — plus warnings and monotonic sequencing
- [x] Four-eyes declared — and unforgeable: `status` is absent from the closed request schema, so the caller cannot request `active`

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. **A sixth graph limitation found** — see §4 |
| Notes / surprises | **The graph gave a confidently wrong answer, and that is the finding worth keeping.** `impact(CLIENT_VISIBLE)` returned `0 impacted`, `risk: LOW`, `epistemic: exact` for a constant with five references across two files. The degraded concept search at least warns; this one issues a guarantee, and a clean blast radius is exactly the result that persuades a reader to stop looking. Six limitations are now recorded across BR-024…031, and the operational rule is that a zero is trustworthy only for a Python function.<br><br>**I had to correct myself.** I said in a hand-off that `auth/errors.py` migrates to RFC 9457 here and that invitation redemption lands here. Neither is true: STEP-004 declares contracts only, and no route handler exists to verify a migration against.<br><br>Four-eyes is declared correctly and **cannot currently be satisfied** — one owner, `ADR-010`. The contract is right; the organisation is the blocker, and STEP-021 cannot ship without an answer.<br><br>The public coverage endpoint was the most interesting thing to get right. Making it public is easy; making it say what is supported without revealing how it is supplied meant one aggregate health value rather than the per-provider breakdown that would have been more useful internally and would have told an attacker precisely when the product is weakest. |
