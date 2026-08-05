# BR-008 — Identity schema and row-level security

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.01 |
| Requirements | REQ-SEC-001, REQ-SEC-002 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-05 |

> **Numbering note:** the sub-step front-matter said `BR-007`, which the STEP-001
> closure had already taken. Renumbered to `BR-008` and the front-matter corrected.

## 1. Intent (protocol step 1)
Create organizations, users, memberships, roles and service identities with **row-level security enforced at the database**, so an application bug cannot cross tenants. This is the foundation 12 downstream steps depend on.

## 2. Graph state (protocol step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `0cac4081ce5abc31d7b65420a6f33ed93bb1eeaf` |
| Graph indexed commit | `0cac408` |
| **Match?** | **Yes** — verified before starting |
| Index timestamp | 2026-08-05 20:26:43 |
| Extractor / schema version | **Not exposed** in `.gitnexus/meta.json` — recorded as a gap, not invented |
| Coverage and known gaps | Documentation only; **0 application symbols** (`RISK-014`) |
| Status | **`BLOCKED` for application code — static fallback applied** |

> Knowledge-graph pre-change check: `BLOCKED`. Static fallback applied. This does **not** satisfy the `REQ-KG-008` release gate.

## 3. Target nodes (protocol step 4)
| Node | Type | Source location | Owner |
| --- | --- | --- | --- |
| `db/migrations/001_identity_tenancy.sql` | Migration | to be created | Deepesh Kumar Gupta |
| `organizations`, `users`, `memberships`, `roles`, `service_identities` | Tables | new | " |
| RLS policies | Security | new | " |

## 4. Dependencies (protocol step 5 — static fallback)
**Inbound (what would depend on this):** none today — verified: **0 application source files**, **0 ORM/model definitions**. Every `auth|identity|tenant` match in the repository is documentation.

**Outbound (what this depends on):** PostgreSQL 18 from `STEP-001.04`. The only existing SQL is `infra/local/postgres/init/01-extensions.sql`, which creates extensions only — **no table-name collision**.

**Fallback honesty:** exhaustive *this time* because zero code exists. **From `STEP-002.02` onward this argument no longer holds** — code will exist, and the fallback becomes genuinely partial.

## 5. Impact by category (protocol step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-001`, `REQ-SEC-002`; STEP-002.01; unblocks .02–.07 | High |
| 2 | Owners / consumers | Sole owner; no external consumers exist | High |
| 3 | Frontend routes / components | **None** — no UI reads these tables yet | High |
| 4 | Backend services / workflows / jobs | **None yet**; `services/identity/` arrives in `.04` | High |
| 5 | APIs / schemas / generated clients / webhooks | **None** — `API-001` is `PROPOSED`, defined in `STEP-004` | High |
| 6 | Events / producers / consumers | **None** — outbox arrives in `STEP-006` | High |
| 7 | Tables / columns / migrations / caches / indexes | **All new.** First migration in the repository; establishes the numbering and RLS convention every later migration inherits | High |
| 8 | Datasets / features / models / prompts / retrievers / tools / evaluations | **None** | High |
| 9 | Tests / fixtures / contract suites | **New** — `tests/security/` created; becomes regression check **R7** from here on | High |
| 10 | Services / deployments / infrastructure | Local Postgres only; no production infrastructure exists | High |
| 11 | Dashboards / alerts / runbooks | `ALRT-SEC-001` and `RB-SEC-001` are specified but **not implemented** (`STEP-024`) — cross-tenant denials will not alert yet | **Medium — gap** |
| 12 | Documentation / deprecation commitments | `DATA_ARCHITECTURE` §8, `AUTHORIZATION_MATRIX`, sub-step record | High |

## 6. Data-flow inspection (protocol step 7 — MANDATORY, security boundary)
The sub-step declares `KG-Q-014` mandatory. **It cannot be run:** `gitnexus trace` / `pdg_query` require indexed application symbols, and there are none.

**Fallback reasoning:** this sub-step *creates* the tenancy surface; there is no prior data flow to inspect. Verified by the zero-source counts in §4 rather than assumed.

**Consequence:** from `STEP-002.02` (tenant-context resolution) the data-flow check becomes both mandatory **and** runnable. If the graph is still `BLOCKED` then, that is a genuine gap rather than a vacuous one.

## 7. Classification (protocol step 8)
`direct` (new schema) · `data/schema` · `security/privacy` · **`unknown`: none** — the filesystem inventory is exhaustive at zero source files.

## 8. Risk scoring (protocol step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | Greenfield schema; no existing readers to break |
| Severity if it occurs | **5** | A missing or bypassable RLS policy is cross-tenant exposure — `RISK-010`, SEV1, halts release |
| Reach | **4** | 12-step fan-in; every later table inherits this convention |
| Detectability | 2 | Isolation tests catch it — **but only the vectors I think to write** |
| Reversibility | 3 | Expand-phase migration reverts; **removing an RLS policy in production widens access, so rollback is forward-only** |
| **Confidence in this analysis** | 2 | Fallback exhaustive at zero source; graph `BLOCKED` caps it above 1 |
| Customer criticality | 1 | No customers yet — but this is the control protecting all future ones |

**Overall: HIGH** — driven by severity × reach, not by likelihood. This is the security boundary the whole product rests on.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| RLS behaviour under connection pooling | `SET LOCAL` is transaction-scoped; a pooler reusing connections could leak context | **Must be tested explicitly**, not assumed |
| `FORCE ROW LEVEL SECURITY` necessity | Table owners bypass RLS silently without it | Tested directly |
| Alerting absent | `ALRT-SEC-001` not implemented until `STEP-024` | Denials logged but not alerted — recorded gap |
| Extractor version unknown | Not exposed by the tool | Recorded, not invented |

## 10. Required actions (protocol step 10)
Migration with RLS; a non-owner application role that cannot bypass; explicit pooling test; `tests/security/` established as R7; document the convention every later migration inherits.

## 11. Approval (protocol step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-05 |

**HIGH risk requires owner approval.** With a single owner the author is also the approver — the `ADR-010` four-eyes gap, in force here on the highest-risk change so far. Stated, not glossed.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | Migration, security suite, docs — no unexpected scope |
| Regression R1–R7 | **PASS** — R4 decreased (REQ-SEC-001/002 now tested) |
| **R7 established** | **YES — 12/12 assertions, meta-tested for detection power** |

## 13. Disposition
**Merged.** HIGH risk realised as predicted: the first isolation run produced false passes (BUG-007). Caught before commit. Alerting gap (category 11) carried to STEP-024.
