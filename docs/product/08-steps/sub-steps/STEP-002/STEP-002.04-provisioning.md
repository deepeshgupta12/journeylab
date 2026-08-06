---
sub_step_id: STEP-002.04
parent_step: STEP-002
title: User, organization, invitation and service-account provisioning
status: IN_PROGRESS
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-003, REQ-TRIP-005]
blast_radius_id: BR-013
depends_on: [STEP-002.03]
last_updated: 2026-08-06
---

# STEP-002.04 — User, organization, invitation and service-account provisioning

## 1. Outcome
Users, organizations, memberships and service identities can be created, updated and revoked through one audited service, and a guest session migrates to an account **without duplicating trips**.

## 2. Scope and boundary
**In scope:** `services/identity/src/provisioning.py` (path implemented as documented), guest→account migration, service identities via workload identity, revocation.
**Not in this sub-step:** consent capture ([STEP-008](../../STEP-008-account-consent-and-traveler-profile.md)), collaborator invitation UX ([STEP-015](../../STEP-015-collaboration-and-decision.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-003 | Service identities use workload identity; **no static long-lived keys exist** | TST-SEC-003 |
| REQ-TRIP-005 | Guest→account migration yields exactly one copy of each trip | TST-TRIP-005 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — `impact(bind_tenant, upstream, 3)` returned `epistemic: exact`, 0 upstream (confirming STEP-004 must still wire it) |
| Queries run | KG-Q-015; KG-Q-014 (credential paths) |
| Direct dependents | STEP-008 onboarding, STEP-015 invitations, STEP-028 org workspace |
| Unknown / low-confidence areas | **`DEC-004` remains unresolved and is NOT bound by this sub-step.** No provider SDK is imported and no branch depends on one; the only IdP knowledge is the opaque `idp_subject` string |
| Blast radius | [BR-013](../../../10-logs/blast-radius/BR-013-identity-provisioning.md) — **HIGH** (identity lifecycle) |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [x] Idempotent by IdP subject — enforced by `ON CONFLICT` at the **database**, not check-then-insert. Two real concurrent connections tested
- [x] Organization + owner membership in one call. The id must be **client-generated**: RLS is `WITH CHECK (id = app_current_org())`, so an org can only be inserted once its own id is the bound tenant
- [x] Grant, reinstate and revoke. Revocation **stamps `revoked_at`, never deletes** — deleting erases the evidence access was held
- [x] Workload identity. **No parameter exists** through which a secret could be passed; asserted by signature introspection
- [~] **PARTIAL — no `trips` table exists** (STEP-007). Memberships re-parent, replay-safe, with before/after counts. The guarantee is built and tested; it has nothing to apply to yet
- [~] **PARTIAL** — state is revoked and `active_role_keys` respects it, so the next authorization check fails. Ending an **already-issued token** needs the session store from `.05`
- [x] No provider SDK imported; no branch on a vendor. `DEC-004` stays open

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
- [x] Sub-step record · `IMPL-011` · `BR-013` · regression entry · tracker

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | **PASS** | `pnpm verify`; 292 tests |
| R7 | **PASS — 12/12** | Plus a new test proving provisioning's owner privilege did not leak into `journeylab_app` |
| R2–R6 | **PASS / N/A** | **R4 deliberately does not count `REQ-TRIP-005` as satisfied.** See [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) |

## 11. Rollback
Provisioning logic reverts cleanly. **Migrated trips do not** — re-parenting is a data change, so migration runs behind a flag with a verified dry-run first.

## 12. Acceptance criteria
- [x] User provisioning idempotent by IdP subject — concurrency-tested
- [x] No static service credentials — schema scanned, and the scan itself meta-tested
- [~] **NOT MET — no trips exist.** Replay produces exactly one copy of each *membership*; trip coverage is STEP-007
- [~] Immediate for authorization checks and audited; **live tokens** are `.05`
- [x] Provider-specific code isolated — none exists in this module

## 13. Completion record
| Field | Value |
| --- | --- |
| Status | **`IN_PROGRESS`, not `VERIFIED`** — `REQ-TRIP-005` is one of this sub-step's two requirements and its acceptance criterion cannot be met yet. Marking it done would put a false green in the tracker, which `MASTER_TRACKER` is the single source of truth against |
| Delivered 2026-08-06 | Everything except trip re-parenting: idempotent provisioning, org + owner creation, grant/revoke, workload identity, replay-safe membership migration |
| Remaining, and its dependency | Trip re-parenting — **blocked on STEP-007** creating `trips`. Nothing else outstanding |
| Implementation | [IMPL-011](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 16 integration tests (292 total); 7/7 mutants killed |
| **Shortfall** | **`REQ-TRIP-005` is NOT satisfied.** There is no `trips` table until STEP-007, so what migrates is memberships. The idempotency contract and replay tests exist so STEP-007 extends the same transaction — but the requirement stays open, and R4 counts it as open |
| Notes / surprises | The sub-step's own prediction held and was designed for. Three things were not predicted. **(1)** I claimed `idp_subject` had no unique index and demonstrated a duplicate-user race — both wrong; my `head -14` had truncated the index list, and the race test disproved my own claim. **(2)** Migration 001 carries `users_identifiable_unless_guest`, which my raw-INSERT fixtures violated; fixtures now go through `provision_user` so they cannot drift from the schema. **(3)** `create_organization` cannot use a server-generated id, because the RLS policy requires the id to already be the bound tenant |
| Carried gaps | Trip re-parenting (STEP-007); migration feature flag + dry-run, required by §11 (STEP-024); audit sink (STEP-002.07); live-token revocation (STEP-002.05) |
