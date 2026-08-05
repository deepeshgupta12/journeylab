---
sub_step_id: STEP-002.06
parent_step: STEP-002
title: Cross-tenant isolation test suite
status: NOT_STARTED
owners: []
requirement_ids: [REQ-SEC-002]
blast_radius_id: BR-012
depends_on: [STEP-002.05]
last_updated: 2026-08-05
---

# STEP-002.06 — Cross-tenant isolation test suite

## 1. Outcome
`TST-SEC-002` exists and runs on every sub-step thereafter as **regression check R7** — the one check that may never fail.

## 2. Scope and boundary
**In scope:** `tests/security/test_tenant_isolation.py` covering API, cache, jobs, exports, events and graph traversal; wiring into the fast test tier.
**Not in this sub-step:** authorization matrix coverage (`.03`), vector/graph isolation for real data (arrives with [STEP-026](../../STEP-026-knowledge-graph-platform.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-002 | Tenant A cannot reach tenant B by **any** path | TST-SEC-002 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015 |
| Direct dependents | Every subsequent sub-step depends on this suite existing |
| Unknown / low-confidence areas | Paths not yet built (vector, graph) — tests are **stubbed with explicit `pending` markers**, never silently omitted |
| Blast radius | BR-012 — test-only, but this is the safety net for everything after |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] Fixtures creating two tenants with overlapping data shapes
- [ ] API vector: cross-tenant read, write, list, export → all denied
- [ ] Cache vector: key collision cannot serve foreign data
- [ ] Job vector: a job for tenant A cannot touch tenant B rows
- [ ] Event vector: consumer cannot process a foreign event into shared state
- [ ] Enumeration: `403` and `404` indistinguishable
- [ ] **Explicit `pending` placeholders** for vector and graph vectors, failing loudly when those stores land
- [ ] Wire into the **fast tier** so it runs at every sub-step

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-002 | security | All vectors above deny cross-tenant access |
| — | meta | A deliberately broken RLS policy makes the suite **fail** — proves the test has teeth |

## 8. Telemetry, security and accessibility
Denials assert an audit event is written. No sensitive data in fixtures.

## 9. Documentation to update
- [ ] Sub-step record · logs · `BR-012` · parent §21 · tracker
- [ ] [SECURITY_TESTING](../../../06-quality/SECURITY_TESTING.md) §2 marked implemented
- [ ] [SUB_STEP_PROTOCOL](../../../02-delivery/SUB_STEP_PROTOCOL.md) R7 becomes executable from here

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | | STEP-001 + 002.01–.05 |
| R7 | | **This sub-step creates R7** |
| R2–R6 | | As applicable |

## 11. Rollback
Removing this suite is a **governance regression** requiring owner approval — it is the mechanism protecting every later change.

## 12. Acceptance criteria
- [ ] All implemented vectors covered and passing
- [ ] Unbuilt vectors marked `pending`, not omitted
- [ ] A seeded RLS break makes the suite fail
- [ ] Suite runs in the fast tier
- [ ] Denials produce audit events

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Notes / surprises | The meta-test matters most: a passing isolation suite that would also pass with RLS disabled is worse than no suite, because it manufactures confidence |
</content>
