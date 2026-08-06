---
sub_step_id: STEP-002.06
parent_step: STEP-002
title: Cross-tenant isolation test suite
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-002]
blast_radius_id: BR-016
depends_on: [STEP-002.05]
last_updated: 2026-08-06
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
| Graph status | ✅ **RUNNABLE** — `impact(authorize, upstream, 3)` returned `epistemic: exact`, LOW, 1 direct caller. No application code modified |
| Queries run | KG-Q-015 |
| Direct dependents | Every subsequent sub-step depends on this suite existing |
| Unknown / low-confidence areas | Paths not yet built (vector, graph) — tests are **stubbed with explicit `pending` markers**, never silently omitted |
| Blast radius | [BR-016](../../../10-logs/blast-radius/BR-016-tenant-isolation-suite.md) — MEDIUM. Test-only, but the safety net for everything after |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [x] Two tenants with **structurally identical** rows — if B's data looked different, a test could pass because a query missed rather than because isolation held
- [x] Storage + authorization vectors: read, write and unbound listing denied; **every operation × every role** (198 combinations) denied against a foreign resource. **Export is a pending vector** — no export path exists
- [~] **Pending** — no cache layer (STEP-010). Fails automatically when one lands
- [x] Covered **at the primitive**: payload round-trip, missing context raises, no ambient store to inherit. End-to-end needs a worker (STEP-006)
- [x] Covered **at the primitive**: conflicting tenant refused, acting tenant stamped. The enforcing outbox is a pending vector (STEP-006)
- [x] Enumeration: one opaque `404`; body carries no tenant, role or permission wording
- [x] **Five pending vectors** (cache, outbox, export, vector store, graph), each detecting whether its subsystem has landed: skip while absent, **FAIL** once present. **Proven** by seeding a fake cache module and an `outbox` table
- [x] Runs under pytest with the `security` marker — R7 is now part of `pnpm verify`, not a separate command to remember

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
- [x] Sub-step record · `IMPL-013` · `BR-016` · regression entry · tracker
- [x] [SECURITY_TESTING](../../../06-quality/SECURITY_TESTING.md) §2 marked implemented
- [x] [SUB_STEP_PROTOCOL](../../../02-delivery/SUB_STEP_PROTOCOL.md) R7 executable in the fast tier

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | **PASS** | 311 Python + 41 TypeScript |
| R7 | **PASS** | Shell suite 12/12; new pytest suite 14 passed, 5 pending |
| R2–R6 | **PASS / N/A** | R2 N/A (no contracts). See [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) |

## 11. Rollback
Removing this suite is a **governance regression** requiring owner approval — it is the mechanism protecting every later change.

## 12. Acceptance criteria
- [x] All implemented vectors covered and passing
- [x] Unbuilt vectors pending **and self-failing** when their subsystem lands
- [x] A seeded RLS break makes the suite fail — built into the suite, run every time
- [x] Suite runs in the fast tier
- [~] Denials are **marked** `audit=True` and asserted. **Nothing persists them** — no audit sink until STEP-002.07

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-06 |
| Implementation | [IMPL-013](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 19 (14 active, 5 pending); 3/3 mutants killed |
| Notes / surprises | The prediction held exactly, and the meta-test is built into the suite so it runs every time rather than being a one-off proof. **Unpredicted:** the pending vectors turned out to be the most valuable part. A placeholder that cannot notice its own dependency arriving is just a comment, so each detects whether its subsystem has landed and converts itself from a skip into a failure. Verified by seeding a fake cache module and an `outbox` table |
| Carried gaps | Cache (STEP-010), outbox enforcement (STEP-006), export (STEP-015/022), vector store (STEP-010), graph traversal (STEP-026), audit persistence (STEP-002.07) |
