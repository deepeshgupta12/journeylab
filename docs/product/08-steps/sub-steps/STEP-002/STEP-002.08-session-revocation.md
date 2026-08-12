---
sub_step_id: STEP-002.08
parent_step: STEP-002
title: Server-side session store and revocation
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-003, REQ-SEC-001, REQ-PRIV-001]
blast_radius_id: BR-036
depends_on: [STEP-002.04, STEP-002.05, STEP-002.07]
last_updated: 2026-08-12
---

# STEP-002.08 — Server-side session store and revocation

> **Why this sub-step exists.** It was not in the original plan. `STEP-002.05`
> recorded server-side revocation as `PARTIAL` and **carried it to
> `STEP-002.07`**; `.07` then closed as `VERIFIED` listing four carried gaps, none
> of which was this one. The commitment was dropped rather than deferred, which is
> `BUG-022`. Authorised by the repository owner on 2026-08-12 as a new sub-step
> rather than by reopening two `VERIFIED` records.

## 1. Outcome
A session can be ended by the server. Signing out, revoking a membership, or an
administrator ending a session all stop an **already-issued** credential from
working — not merely the next one.

## 2. Scope and boundary
**In scope:** the session store (`sessions`, `guest_sessions`); revocation of one
session, of every session for a user, and as a consequence of membership
revocation; revocation checked at validation; audit events for each.

**Not in this sub-step:** wiring into HTTP routes (`apps/api` has no routes until
STEP-004 handlers land); admin-initiated revocation UI (`STEP-021`); trip
re-parenting, which is `.04`'s other partial and is blocked on the `trips` table
in `STEP-007`.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-SEC-003 | A revoked session cannot authenticate a request, before its natural expiry | §7 |
| REQ-SEC-001 | Every authenticated session row carries a tenant; no cross-tenant read or revoke | §7, R7 |
| REQ-PRIV-001 | No raw token is ever stored | §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `5086a8a` — indexed commit matched HEAD at pre-change |
| Queries run | `impact(validateGuestSession, upstream, includeTests)` — 1 direct (its own test), LOW, `epistemic: exact`. `impact(resolve_context, upstream, includeTests)` — **0 impacted**, LOW, `epistemic: exact` |
| Interpretation of the zero | `resolve_context` is a Python function, and `CLAUDE.md` records that a zero result is trustworthy for a Python function specifically. It is zero because **`apps/api` still declares no routes** — consistent with `BR-028` §7, not a graph gap |
| Unknown / low-confidence areas | The web session lives in TypeScript and the store will be Python. The graph cannot trace that boundary (`BR-025`), so the coupling between `validateGuestSession` and the store it validates against is **unverifiable by the graph** and is covered by tests instead |
| Blast radius | **[BR-036](../../../10-logs/blast-radius/BR-036-session-revocation.md)** |
| Approval required? | Per blast-radius score |

## 5. Implementation plan
- [x] `sessions` — authenticated, tenant-scoped, RLS, token hashed at rest
- [x] `guest_sessions` — **a separate table, deliberately** (§6)
- [x] Revoke one session; revoke every session for a user; both stamp `revoked_at`. **The app role has no DELETE privilege at all**, so "never deletes" is enforced by the grant rather than by remembering
- [x] **Revocation checked at validation**, so an unexpired revoked session fails
- [x] Revoking a membership revokes that user's sessions in the same transaction — closes `.04`'s second partial
- [x] `validateGuestSession` rejects a revoked record — `revokedAt` is **required**, so the compiler found all five call sites
- [x] An audit event per revocation, from a closed reason vocabulary

## 6. The design question this sub-step had to answer

**A guest session has no tenant, and `REQ-SEC-001` says every row carries one.**

A guest session precedes authentication: there is no organization to scope it to.
Three ways out, and the choice matters more than it looks:

| Option | Rejected because |
| --- | --- |
| Nullable `organization_id` on one table | Makes "every row has a tenant" false wherever it is checked, and the RLS predicate has to special-case NULL — which is exactly the shape of a policy that later lets a real row through |
| A sentinel "no tenant" organization | Invents a tenant that does not exist and gives every guest session the same one, so a bug that leaks across guest sessions looks like a legitimate same-tenant read |
| **Two tables** | **Chosen.** `sessions` is tenant-scoped with `organization_id NOT NULL` and RLS; `guest_sessions` has no tenant column because a guest has no tenant |

Two tables keep each invariant true rather than weakening one to cover both. The
cost is a second code path for revocation, which is real but visible.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-SEC-003a | Python | A revoked session fails validation **before** its expiry |
| TST-SEC-003b | Python | Revoking one session leaves the user's other sessions alive |
| TST-SEC-003c | Python | Revoke-all ends every session for that user and no other user's |
| TST-SEC-003d | Python | Revoking a membership revokes that user's sessions |
| TST-SEC-003e | Python | Revocation stamps `revoked_at`; the row still exists |
| TST-SEC-001x | Python (R7) | A session row is invisible and unrevokable from another tenant |
| TST-PRIV-001b | Python | No raw token is stored; only its hash |
| — | TypeScript | `validateGuestSession` rejects a revoked record |
| — | meta | Each of the above seeded and confirmed to fail |

## 8. Telemetry, security and accessibility
Every revocation emits an audit event carrying the reason. No token, raw or
hashed, appears in an audit payload or a log line. No user-facing surface here.

## 9. Documentation to update
- [x] Sub-step completion record
- [x] IMPLEMENTATION_LOG `IMPL-033` · REGRESSION_LOG · BUG_REGISTER `BUG-022`
- [x] ENHANCEMENT_LOG `ENH-002` — **logged, not built; owner decision pending**
- [x] `BR-036`
- [x] Parent step §21 · MASTER_TRACKER · `.04` and `.05` partial markers

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 665 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched; the STEP-004.08 gate confirms it |
| R3 graph diff as expected | **PASS** | One migration, one module, one cascade, one interface |
| R4 untested requirements | **PASS — improved** | REQ-SEC-003 was *claimed* by `.05` and untested; now covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…022; meta-suite 55/55 |
| R7 tenant isolation | **PASS — 18/18** locally, up from 12 | Cross-tenant read, **cross-tenant revoke**, no DELETE privilege. **Runs locally only — CI has no database, so R7 and 41 other tests skip there.** Pre-existing; see the regression entry |

**Overall:** **PASS**.

## 11. Rollback
Revert the commit and drop migration `003`. No prior sub-step depends on the
store; `.04` and `.05` return to their current partial state.

## 12. Acceptance criteria
- [x] A revoked session cannot authenticate before its natural expiry — seeded and killed
- [x] Revocation cascades from membership revocation — seeded and killed
- [x] A session cannot be read or revoked across a tenant boundary — R7 18/18
- [x] No raw token stored anywhere — asserted against the live table
- [x] STEP-002 reaches **8/8**, with `.04`'s remaining partial explicitly blocked on STEP-007

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-12 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | **BUG-022** — the carried commitment this sub-step exists to discharge |
| Notes / surprises | **The code was right at every step and the commitment was lost anyway.** `.05` deferred revocation to `.07`, `.07` closed `VERIFIED` without it, and nothing failed — because a carry is prose and `substep-docs.sh` can only check that records exist, not that promises in them were kept. For six sub-steps `session.ts` carried a comment asserting server-side revocation was authoritative while there was no session table in any migration. `ENH-002` proposes the guard; it is logged, not built.<br><br>**A guest session has no tenant, and that had to be answered rather than worked around.** A nullable `organization_id` would force the RLS predicate to special-case NULL, which is the shape of a policy that later lets a real row through; a sentinel "no tenant" org would give every guest the same one, so a leak between guests would look like a legitimate same-tenant read. Two tables keep both invariants true. The cost is two revocation paths, visible rather than hidden behind a mode flag.<br><br>**My first mutation test was invalid and looked fine.** Dropping `FORCE` RLS on `sessions` in the database left R7 passing, because the suite re-applies the migration before asserting — it repaired the drift it then checked. The seed had to go in the migration file. A suite that heals the condition it tests cannot fail on it, and nothing revealed that until a mutant was tried.<br><br>**The FORCE-RLS check named three tables**, so the fourth would have gone unchecked while the assertion passed. Now derived from the schema — every table with an `organization_id` — so the next tenant table is covered by whoever creates it. Same pattern as `BUG-021`, caught this time because I went looking.<br><br>**I wrote the test fixture against an API I imagined**, calling `provision_organization` with a `name`; it is `create_organization` with `slug` and `display_name`, and I invented a `traveller` role that does not exist. Third occurrence of this exact failure after the STEP-003 e2e probes and the STEP-004.08 consumer expectations. Reading the module first would have cost less than the two cycles it took.<br><br>**R7 gained a kind of assertion it did not have.** Revoking across a tenant boundary is denial of service, not disclosure; the suite had only ever asserted that a tenant could not *read* another's rows. |
