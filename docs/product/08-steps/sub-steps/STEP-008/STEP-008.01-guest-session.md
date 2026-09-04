---
sub_step_id: STEP-008.01
parent_step: STEP-008
title: Guest session with a no-email planning path
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PRIV-001]
blast_radius_id: TBD
depends_on: [STEP-007.05]
last_updated: 2026-09-04
---

# STEP-008.01 — Guest session with a no-email planning path

## 1. Outcome
A traveller plans a complete trip without providing an email address or creating an account.

## 2. Scope and boundary
**In scope:** Guest session issue and lifetime; guest-scoped trip ownership; the `is_guest` path through `STEP-002`'s session layer.

**Not in this sub-step:** Account creation and migration (`.02`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PRIV-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Guest session lifetime. Too short loses a half-built trip; too long is an unclaimed personal-data store with no owner to delete it. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Guest session issued without any identifier (`users.is_guest`, already modelled in `010`)
- [ ] A guest owns trips through the same tenancy path as an account — **no second authorization model**
- [ ] Session lifetime and expiry recorded, and expiry deletes the trip (`REQ-PRIV-006`)
- [ ] Every planning operation available to a guest, with no feature gated behind an email
- [ ] Server-side revocation applies to guest sessions too (`BUG-022`'s lesson)

## 6. Contracts and schema changes
Consumes the session contract from `STEP-002.05`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-001 | e2e | **A complete trip is planned end to end with no email** |
| — | security | A guest session is tenant-scoped and cannot reach another guest's trip |
| — | integration | Guest session expiry deletes the trip and its derived rows |
| — | security | A guest session can be revoked server-side |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
A guest session ID is pseudonymous but it is still an identifier; it is never joined to an IP in any store.

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
Revert the commit; guest planning stops and existing guest trips become unreachable. **Unreachable is not deleted** — the revert must include the deletion, or it creates orphaned personal data.

## 12. Acceptance criteria
- [ ] A trip is planned end to end with no email
- [ ] Guest trips are tenant-isolated
- [ ] Expiry deletes, rather than orphaning
- [ ] Guest sessions are revocable

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
| Notes / surprises | **A guest trip is personal data with no one to ask about it.** There is no account to log into, no email to send a deletion link to, and no owner to authenticate — so expiry is the *only* deletion path, which makes the expiry job load-bearing for `REQ-PRIV-006` in a way no account-based path is. |
