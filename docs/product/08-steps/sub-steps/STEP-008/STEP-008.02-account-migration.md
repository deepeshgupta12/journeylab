---
sub_step_id: STEP-008.02
parent_step: STEP-008
title: Account creation and guest-to-account migration without duplication
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PRIV-001, REQ-TRIP-003]
blast_radius_id: TBD
depends_on: [STEP-008.01]
last_updated: 2026-09-04
---

# STEP-008.02 — Account creation and guest-to-account migration without duplication

## 1. Outcome
A guest who creates an account keeps the trip they were working on, exactly once.

## 2. Scope and boundary
**In scope:** Account creation via Auth0 (`ADR-013`); guest→account trip transfer; duplicate prevention.

**Not in this sub-step:** Profile capture (`.03`); consent (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PRIV-001, REQ-TRIP-003 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | **Auth0 has never been exercised against a live tenant** (`DEC-004`'s open caveat). Passkey enrolment and rotation-under-concurrency are unproven, and this is the sub-step where that stops being deferrable. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Account creation through the `STEP-002` verifier port, so the IdP stays behind it
- [ ] Migration moves trip ownership in **one transaction** (`STEP-006.04`: one aggregate, one transaction)
- [ ] **Idempotent on retry** — a migration replayed after a timeout must not duplicate the trip
- [ ] The guest session is revoked as part of the migration, not left live
- [ ] Migration is audited: who, when, from which guest session

## 6. Contracts and schema changes
Consumes the session and identity contracts. Emits no new event.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-TRIP-003 | e2e | A guest's in-progress trip survives account creation |
| — | integration | **Replaying the migration produces one trip, not two** |
| — | integration | The guest session is revoked once the account owns the trip |
| — | security | A guest cannot migrate another guest's trip |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
The migration is an audit event; the trip content is not in it.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit. Accounts already created remain; **migrated trips must not be un-migrated**, because reverting ownership would hand personal data back to an expired session.

## 12. Acceptance criteria
- [ ] The in-progress trip survives account creation
- [ ] Migration is idempotent under retry
- [ ] The guest session is revoked
- [ ] Migration is audited

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Mutation testing | — |
| Bugs found | — |
| Notes / surprises | **A migration that times out and is retried is the normal path, not the edge case** — the same reasoning as the outbox's re-delivery in STEP-006.06. The user taps again because nothing happened on screen, and the second attempt must find the work already done. `STEP-006.07`'s idempotency is the mechanism, but the effect here is a *move*, not an insert, so replaying it must be a no-op rather than a second move. |
