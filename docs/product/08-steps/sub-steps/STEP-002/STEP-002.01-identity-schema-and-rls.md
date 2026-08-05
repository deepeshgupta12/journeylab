---
sub_step_id: STEP-002.01
parent_step: STEP-002
title: Identity schema and row-level security
status: NOT_STARTED
owners: []
requirement_ids: [REQ-SEC-001, REQ-SEC-002]
blast_radius_id: BR-007
depends_on: [STEP-001.06]
last_updated: 2026-08-05
---

# STEP-002.01 — Identity schema and row-level security

## 1. Outcome
Organizations, users, memberships, roles and service identities exist in PostgreSQL with row-level security enforcing tenant isolation **at the database**, so an application bug cannot cross tenants.

## 2. Scope and boundary
**In scope:** `db/migrations/001_identity_tenancy.sql`, RLS policies, tenant-context session variable, seed roles.
**Not in this sub-step:** API-layer context resolution (`.02`), policy definitions (`.03`), provisioning logic (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-001 | Every tenant-scoped table has a non-null `organization_id` | TST-SEC-001 |
| REQ-SEC-002 | RLS denies cross-tenant reads and writes at the database level | TST-SEC-002 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed) |
| Queries run | KG-Q-015; **KG-Q-014 mandatory** — this is a security boundary |
| Direct dependents | Every future migration and repository |
| Unknown / low-confidence areas | Extension and RLS behavior under connection pooling — **verify, do not assume** |
| Blast radius | BR-007 — **HIGH**: foundational security boundary, 12-step fan-in |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] `organizations`, `users`, `memberships`, `roles`, `service_identities` tables
- [ ] `organization_id` non-null on every tenant-scoped table with an FK
- [ ] Tenant context via a session-local setting (`SET LOCAL`), never a connection-global
- [ ] `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` on every tenant table
- [ ] Policies for `SELECT`, `INSERT`, `UPDATE`, `DELETE` keyed on the session tenant
- [ ] A dedicated application role that **cannot bypass RLS** (not the table owner)
- [ ] Indexes on `organization_id` leading every composite key

## 6. Contracts and schema changes
| Artifact | Change | Compatibility | Version action |
| --- | --- | --- | --- |
| `db/migrations/001_identity_tenancy.sql` | New | Additive (first migration) | n/a |

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-001 | integration | Insert without tenant context fails |
| TST-SEC-002 | security | Session for tenant A cannot read/update/delete tenant B rows |
| — | integration | Application role cannot bypass RLS even with direct SQL |
| — | integration | Pooled connections do not leak tenant context between checkouts |

## 8. Telemetry, security and accessibility
Cross-tenant denials are counted and alertable (`ALRT-SEC-001`). No UI in this sub-step.

## 9. Documentation to update
- [ ] Sub-step record · `IMPLEMENTATION_LOG` · `REGRESSION_LOG` · `BR-007` · parent §21 · tracker
- [ ] [DATA_ARCHITECTURE](../../../03-architecture/DATA_ARCHITECTURE.md) §8 tenancy confirmed against implementation

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | | Includes all STEP-001 sub-steps |
| R2 contract compatibility | | N/A — no contracts yet |
| R3 graph diff | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned | | Not increased |
| R6 closed-bug tests | | N/A |
| R7 tenant isolation | | **First real run — establishes the R7 baseline** |

## 11. Rollback
Expand-phase only; the migration adds tables and policies. Reverting drops them. **Removing an RLS policy widens access** — in production this is forward-only (fix the policy, never drop it).

## 12. Acceptance criteria
- [ ] Every tenant-scoped table carries non-null `organization_id`
- [ ] RLS enabled **and forced** on all tenant tables
- [ ] Application role cannot bypass RLS
- [ ] Cross-tenant access denied at the database, proven by test
- [ ] Tenant context does not leak across pooled connections

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Notes / surprises | `FORCE ROW LEVEL SECURITY` matters: without it the table owner silently bypasses every policy, which is the most common way RLS is believed-present but absent |
</content>
