---
sub_step_id: STEP-002.04
parent_step: STEP-002
title: User, organization, invitation and service-account provisioning
status: NOT_STARTED
owners: []
requirement_ids: [REQ-SEC-003, REQ-TRIP-005]
blast_radius_id: BR-010
depends_on: [STEP-002.03]
last_updated: 2026-08-05
---

# STEP-002.04 — User, organization, invitation and service-account provisioning

## 1. Outcome
Users, organizations, memberships and service identities can be created, updated and revoked through one audited service, and a guest session migrates to an account **without duplicating trips**.

## 2. Scope and boundary
**In scope:** `services/identity/src/provisioning.py`, guest→account migration, service identities via workload identity, revocation.
**Not in this sub-step:** consent capture ([STEP-008](../../STEP-008-account-consent-and-traveler-profile.md)), collaborator invitation UX ([STEP-015](../../STEP-015-collaboration-and-decision.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-003 | Service identities use workload identity; **no static long-lived keys exist** | TST-SEC-003 |
| REQ-TRIP-005 | Guest→account migration yields exactly one copy of each trip | TST-TRIP-005 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015; KG-Q-014 (credential paths) |
| Direct dependents | STEP-008 onboarding, STEP-015 invitations, STEP-028 org workspace |
| Unknown / low-confidence areas | **`DEC-004` identity provider is unresolved** — provisioning must stay vendor-substitutable |
| Blast radius | BR-010 — HIGH (identity lifecycle) |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] Provision user on first successful authentication (idempotent by IdP subject)
- [ ] Organization creation with an owner membership
- [ ] Membership grant/revoke with audit
- [ ] Service identity registration via **workload identity**, never static keys
- [ ] **Guest→account migration:** re-parent trips by claim, idempotent, never duplicating
- [ ] Revocation invalidates sessions and tokens immediately
- [ ] Keep provider-specific code behind an interface so `DEC-004` stays reversible

## 6. Contracts and schema changes
Consumes `API-001`. No new schema beyond `.01` tables.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-003 | integration | No static service key exists; workload identity works |
| TST-TRIP-005 | e2e | Migration produces one copy of each trip; replay is idempotent |
| — | security | Revocation ends access immediately |

## 8. Telemetry, security and accessibility
Provisioning and revocation are audited. Migration is logged with before/after trip counts so duplication is detectable.

## 9. Documentation to update
- [ ] Sub-step record · logs · `BR-010` · parent §21 · tracker

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | | STEP-001 + 002.01–.03 |
| R7 | | Must pass |
| R2–R6 | | As applicable |

## 11. Rollback
Provisioning logic reverts cleanly. **Migrated trips do not** — re-parenting is a data change, so migration runs behind a flag with a verified dry-run first.

## 12. Acceptance criteria
- [ ] User provisioning idempotent by IdP subject
- [ ] No static service credentials anywhere
- [ ] Guest→account migration produces exactly one copy of each trip
- [ ] Revocation immediate and audited
- [ ] Provider-specific code isolated behind an interface

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Notes / surprises | Migration idempotency matters more than it looks: a retried migration that duplicates trips is indistinguishable from a user creating them |
</content>
