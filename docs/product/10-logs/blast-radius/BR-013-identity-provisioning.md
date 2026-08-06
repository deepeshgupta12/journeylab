# BR-013 — User, organization, invitation and service-account provisioning

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.04 |
| Requirements | REQ-SEC-003, REQ-TRIP-005 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-010`, which belongs to the Postgres readiness fix. This record is `BR-013`; the front-matter has been corrected.

## 1. Intent (step 1)
One audited service for the identity lifecycle — provision, grant, revoke, register a workload identity, and migrate a guest onto a real account without duplicating anything — while `DEC-004` stays unbound.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `19a6037` |
| Graph indexed commit | `19a6037` — `status` reported stale first; re-indexed before analysis |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** by the tool — recorded, not invented |
| Coverage and known gaps | Python indexed. **Caveat:** the graph indexes committed state, so this sub-step's own files were invisible to the pre-change query — correct for a *pre-change* check, but it means "0 callers" means "0 committed callers" |
| Status | **RUNNABLE** |

> **HEAD moved mid-sub-step.** `BUG-012` (CI red) was found and fixed while this work was in progress, advancing HEAD to `972b93f`. The pre-change analysis was performed at `19a6037` and the intervening commit touched only `tools/gen_authz_matrix.py` and the bug register — no identity code. Recorded rather than silently re-baselined.

## 3. Target nodes (step 4)
| Node | Type | Location |
| --- | --- | --- |
| `provisioning` | Module (new) | `services/identity/src/provisioning.py` |
| `users`, `organizations`, `memberships`, `service_identities` | Tables — **written**, not altered | migration 001 |
| `bind_tenant`, `RequestContext` | **Existing — consumed, not modified** | `apps/api/src/auth/` |

## 4. Dependencies (step 5 — graph-derived, three hops)
`impact({target: "bind_tenant", direction: "upstream", maxDepth: 3})` → `epistemic: exact`, **0 upstream**, risk LOW.

That zero is meaningful twice over: it confirms BR-011's carried finding that `bind_tenant` still has no production caller (STEP-004 must wire it), and it establishes that this sub-step adds the **first** real consumer of the tenant binding — `create_organization` cannot function without it.

**Outbound:** migration 001's schema and its constraints; `auth.db.bind_tenant`; `auth.context.RequestContext`. No provider SDK, by requirement.

**Inbound:** none — no endpoint or worker calls provisioning yet.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-003`, `REQ-TRIP-005`; STEP-002.04. Prerequisite for STEP-008 onboarding, STEP-015 invitations, STEP-028 org workspace | High |
| 2 | Owners / consumers | Sole owner; no external consumers | High |
| 3 | Frontend routes / components | **None today.** Guest→account migration will surface at STEP-008 onboarding | High |
| 4 | Backend services / workflows / jobs | **First module under `services/`.** Establishes the layering: domain services separate from the `apps/api` boundary | High |
| 5 | APIs / schemas / clients / webhooks | **None** — consumes `API-001`, still `PROPOSED` | High |
| 6 | Events / producers / consumers | **None.** Provisioning emits no events; `AuditRecord` is returned to the caller, not published | High |
| 7 | Tables / columns / migrations / caches / indexes | **No schema change** — §6 forbids it and none was needed. Writes to all four identity tables; relies on `users.idp_subject` unique, `memberships` unique `(org, user, role)`, and the `users_identifiable_unless_guest` check | High |
| 8 | Datasets / models / prompts / retrievers / tools / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+16 integration tests** (292 total). First tests that write to the identity tables | High |
| 10 | Services / deployments / infrastructure | New `services/identity/src` on the Python path. No new runtime dependency | High |
| 11 | Dashboards / alerts / runbooks | **No audit sink exists** (STEP-002.07). Every mutating call returns an `AuditRecord` the caller must persist — **nothing yet persists them** | **Medium — carried gap** |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker; this record | High |

## 6. Data-flow inspection (step 7 — MANDATORY, credential paths)
The sub-step names `KG-Q-014` over **credential paths**. Run against the live schema, not by inspection of intent:

| Question | Evidence |
| --- | --- |
| Does any identity table store a credential? | Queried `information_schema.columns` for all five tables; no column matches `secret\|password\|api_key\|private_key\|token\|credential`. `service_identities` holds `workload_subject` — a *name* the platform attests, not a bearer secret |
| Can a credential be introduced through this module? | `register_service_identity` has **no parameter** through which one could be passed. Asserted by introspecting the signature, so adding one breaks a test |
| Is the credential scan itself real? | Meta-tested: the pattern must match `api_key`, `client_secret`, `password`, `private_key`, `refresh_token`, and must **not** match `role_key`, `idp_subject`, `workload_subject` |
| Does provisioning weaken the STEP-002.01 boundary? | It runs as the table owner (it must — it creates rows no tenant context can yet see). A test asserts `journeylab_app` still has `NOBYPASSRLS` and FORCE RLS is still set on all three tenant tables |

## 7. Classification (step 8)
`direct` (new write path to identity tables) · `security/privacy` · `data` (migration re-parents rows) · **`unknown`:** trip re-parenting, because no `trips` table exists.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | No caller yet; writes are constrained by unique indexes and a check constraint |
| Severity if it occurs | **4** | A duplicated identity or a mis-scoped membership grants access that was never intended. Below STEP-002.01's 5 because RLS still contains the blast |
| Reach | 4 | Every account, org and workload identity in the product is created here |
| Detectability | 2 | 16 integration tests against the real database; 7/7 mutants killed |
| Reversibility | **4** | Logic reverts cleanly; **migrated rows do not** — re-parenting is a data change (sub-step §11) |
| **Confidence in this analysis** | 4 | Graph `epistemic: exact`; schema verified live rather than from the migration file |
| Customer criticality | 1 | No customers yet |

**Overall: HIGH** — reach and irreversibility of the migration path.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **No `trips` table exists** | Trips arrive at STEP-007 | **Open and material.** REQ-TRIP-005 says "exactly one copy of each trip"; what migrates today is **memberships**. The idempotency contract and its replay tests are built now so STEP-007 extends the same transaction rather than inventing the guarantee later. **REQ-TRIP-005 is not fully satisfied by this sub-step** and must not be marked complete on its strength |
| Migration runs without a feature flag or dry-run | Sub-step §11 requires "a flag with a verified dry-run first" | **Open.** No flag system exists (STEP-024). `MigrationReport` supplies the before/after counts a dry-run would need; the flag is not implemented. Stated rather than claimed |
| Audit records are returned, not persisted | No audit sink until STEP-002.07 | **Open.** Returning the value rather than logging it means the obligation is visible in the type, but nothing enforces the caller writes it |
| Revocation does not end a live session | No session store until STEP-002.05 | **Open.** `revoke_membership` stamps state and `active_role_keys` respects it, so the *next* authorization check fails. An already-issued token is unaffected |
| Provisioning runs as table owner | It must, to create rows RLS would hide | **Accepted, tested.** A test asserts the application role gained no bypass |
| `create_organization` requires a client-generated id | Forced by `WITH CHECK (id = app_current_org())` — an org can only be inserted when the tenant context already equals its id | **Understood, documented.** Surprising enough to be worth a comment in the code |

## 10. Required actions (step 10)
Database-level idempotency, not check-then-insert; workload identity with no credential parameter; revocation that retains evidence; replay-safe migration with before/after counts; keep every provider detail out; prove the boundary from STEP-002.01 is not weakened.

## 11. Approval (step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-06 |

HIGH risk, single owner — author and approver coincide (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | One new service module, one test module, pyproject paths. **No existing symbol modified** |
| Regression R1–R7 | **PASS** — 292 tests; R7 12/12; meta-suite 25/25 |
| Mutation testing | **7/7 killed** |

## 13. Disposition
**Merged with an explicit shortfall.** `REQ-SEC-003` is satisfied. **`REQ-TRIP-005` is not** — the guarantee is built and tested, but there are no trips to apply it to. Recorded here and in the sub-step rather than counted as done.
