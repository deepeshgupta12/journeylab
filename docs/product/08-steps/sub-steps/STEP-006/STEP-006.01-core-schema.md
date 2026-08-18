---
sub_step_id: STEP-006.01
parent_step: STEP-006
title: Core transactional schema, constraints, indexes and RLS
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-001, REQ-DATA-007]
blast_radius_id: BR-050
depends_on: [STEP-005.10]
last_updated: 2026-08-18
---

# STEP-006.01 — Core transactional schema, constraints, indexes and RLS

## 1. Outcome
All sixteen canonical entities exist with constraints, indexes and row-level security, and immutability is enforced **at the schema level** where reproducibility depends on it.

## 2. Scope and boundary
**In scope:** `db/migrations/010_domain.sql`; tables for DATA-001…016; FKs, check constraints, indexes; RLS on every tenant-scoped table.

**Not in this sub-step:** Domain logic (`.03`); normalizers (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-SEC-001, REQ-DATA-007 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED — and that overstates it, see below** |
| HEAD / indexed commit | `c346697` — matched HEAD at pre-change |
| Queries run | `impact` on `bind_tenant`, `app_current_org`, `RequestContext`; `cypher` over `*.sql` |
| **Finding** | **`RISK-017`** — every `.sql` file is **one node**. No tables, columns, constraints or policies exist as symbols, and `app_current_org` returns `UNKNOWN`. For the change type §20 calls low-reversibility, the `REQ-KG-008` gate confirms only that the file exists |
| **What replaced it** | Blast radius derived from the migration and from **11 mutations applied to the deployed schema** — see `BR-050` §7 |
| Unknown / low-confidence areas | Retention defaults await the privacy owner (§27), so `retention_days` is nullable and NULL means **undecided, not unlimited** |
| Blast radius | **[BR-050](../../../10-logs/blast-radius/BR-050-core-schema.md)** — **HIGH**, confidence MEDIUM |
| Approval required? | **Yes, and given by the owner directing this step.** With one owner the author is also the approver — the `ADR-010` four-eyes gap, in force exactly as on `BR-008`. Stated, not glossed |

## 5. Implementation plan
- [x] Tables for all sixteen entities — DATA-001/002 already existed; fifteen created here, plus `place_provider_ids` and `evidence_pack_facts`
- [x] `organization_id` non-null with ENABLE **and** FORCE RLS on all thirteen tenant-scoped tables. `places` is deliberately **not** tenant-scoped (reference data, `BR-046` §7)
- [x] **Immutability enforced by trigger *and* revoked grant** — each covers what the other cannot; the grant stops the application, the trigger stops the migration owner. **UPDATE only: DELETE stays permitted so `REQ-PRIV-006` erasure remains possible**
- [x] Scenario lineage — brief, pack, solver config, seed — all NOT NULL
- [x] Booking references in schema `booking` with role `journeylab_booking`; `journeylab_app` has no USAGE, and the booking role has no read on planning tables
- [x] Indexes leading with `organization_id`; `evidence_facts` indexed separately on effective and observed time because they answer different questions

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-SEC-001 | integration | No tenant row insertable without tenant context |
| — | integration | **UPDATE on an immutable table fails** |
| — | integration | **DELETE on an immutable table succeeds** — the distinction that keeps `REQ-PRIV-006` implementable |
| TST-SEC-010 | security | Planning role cannot reach the booking schema |
| — | security | Booking role cannot read planning tables — segregation cuts both ways |
| — | security | **No payment-credential column exists in any schema** |
| — | integration | No tenant-scoped table is missing FORCE RLS — derived from the catalogue, not listed |
| — | integration | A scenario cannot be stored without each of its four lineage columns |
| — | integration | Null Island refused; money without a currency refused |

18 tests, all against real PostgreSQL. **Mutation testing: 11 seeded, 11 killed —
against the deployed schema**, because the migration is `CREATE ... IF NOT EXISTS`
and mutating the file changes nothing.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-040` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 1080 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Column names match `temporal-validity.json` and `provenance.json`, so schema and contract cannot drift under different names |
| R3 graph diff as expected | **PASS — by inspection** | `RISK-017`: the graph cannot report a schema diff |
| R4 untested requirements | **PASS — improved** | REQ-DATA-007, REQ-SEC-001 |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…027; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18, now over 18 tenant tables rather than 6** | The script now applies 010; without it the derived assertion passed having checked tables that did not exist |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Sixteen entities created with constraints
- [x] Immutable tables reject UPDATE at the database — **and still accept DELETE**
- [x] Scenario lineage columns are NOT NULL
- [x] Booking schema segregated by grant, in both directions
- [x] RLS forced on all tenant tables, asserted by derivation rather than by list

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-18 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **11 of 11 killed**, against the deployed schema |
| Bugs found | None in the migration. One in my own mutation harness — see below |
| Risks raised | **`RISK-017`** — the code graph cannot see a migration |
| Notes / surprises | **The mandated pre-change check has nothing to say about a migration.** Every `.sql` file is one node: no tables, columns, constraints or policies, and `app_current_org` returns `UNKNOWN` because it is a SQL function. For the change type §20 calls low-reversibility, the `REQ-KG-008` release gate confirms the file exists and nothing else. Worse than `RISK-016`, because a wrong number can be contradicted by grep and no answer at all looks exactly like a clean one.<br><br>**Mutating the file proves nothing.** The migration is `CREATE ... IF NOT EXISTS`, so re-applying a mutated copy leaves the schema untouched and every test passes. The mutants weaken the **deployed** schema instead — which is the only place the question "is this guarantee live" can be asked.<br><br>**My mutation harness damaged the database and reported success.** A mutant that permits a *write* leaves the row behind, and the row then blocks its own restore: dropping the Null Island check let a `0,0` place in, and re-adding the constraint failed against it. The run printed `11/11 killed` and `SCHEMA NOT RESTORED` together, and only the final verification line made the second half visible. Without it, a suite that weakens what it tests would have read as a pass.<br><br>**A derived check is only as complete as the schema in front of it.** The R7 FORCE-RLS assertion is derived from the catalogue precisely so new tables are covered automatically — but the script applied only 001 and 003, so on a standalone run the thirteen new tables would not exist and the assertion would pass having checked nothing. Derivation removes the stale-list risk, not the incomplete-schema risk.<br><br>**`auth/db.py` had already documented the trap I fell into.** `SET LOCAL app.current_org = %s` is a syntax error; the module solved it at STEP-002 and explained why. I wrote the test first and read the explanation second. |
