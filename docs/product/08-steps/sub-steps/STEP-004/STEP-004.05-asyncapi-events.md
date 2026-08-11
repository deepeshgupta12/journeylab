---
sub_step_id: STEP-004.05
parent_step: STEP-004
title: AsyncAPI event contracts with delivery guarantees (EVT-001…008)
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-006, REQ-DATA-008]
blast_radius_id: BR-032
depends_on: [STEP-004.04]
last_updated: 2026-08-11
---

# STEP-004.05 — AsyncAPI event contracts with delivery guarantees (EVT-001…008)

## 1. Outcome
All eight domain events are specified with envelope, schema, partition key and an **explicit delivery guarantee** each.

## 2. Scope and boundary
**In scope:** `contracts/asyncapi.yaml`; shared envelope; per-event payload schemas; delivery and ordering semantics.

**Not in this sub-step:** Outbox implementation ([STEP-006](../../STEP-006-canonical-data-model-and-event-backbone.md)); consumer implementations.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-006, REQ-DATA-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date at `d2f950b` |
| HEAD / indexed commit | `d2f950b` / `d2f950b` — matched |
| Queries run | `detect_changes()`. **No symbol-level query was applicable** — one YAML document and one test module, no Python symbol changed. Recorded rather than substituted for by an irrelevant query returning LOW |
| Unknown / low-confidence areas | **Resolved and enforced.** DEC-009 changes the transport, not the contract: no `servers` block and no channel `bindings` — the two places AsyncAPI lets a transport leak in — with a test asserting both absences, so answering DEC-009 later cannot bind the contract to the answer |
| Blast radius | **[BR-032](../../../10-logs/blast-radius/BR-032-asyncapi-events.md) — MEDIUM, confidence HIGH.** The record predicted `BR-026`; taken by STEP-003.09 |
| Approval required? | **No** |

## 5. Implementation plan
- [x] Shared envelope — all nine fields, with `causation_id` optional because an event caused by a user action has no causing event
- [x] Eight schemas with **IDs and classifications only** — enforced by scanning every payload property against 24 content-shaped names, plus a meta-test proving the scan works. All payloads closed
- [x] Delivery guarantee per event — three at-least-once, three **exactly-once-effect**, two deduplicated streams with declared dedupe keys
- [x] Partition key and per-trip ordering as the only guarantee — **with two deliberate exceptions**: a deletion request spans every trip a subject has, and provider health is not a property of a trip
- [x] `EVT-003` carries seed, solver version, model versions and pack ID, so `REQ-CONS-006` is auditable from the stream alone

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-PLAT-006 | contract | Every event declares a delivery guarantee, order key and retention | ✅ all 8 |
| — | contract | **No event schema permits personal data** — or trip content, prose or coordinates | ✅ 24 names × 8 events, **plus a meta-test that the scan can find a seeded field** |
| — | contract | `exactly-once` is described as an **effect**, because no transport delivers it | ✅ |
| — | contract | The deletion event's subject reference is pseudonymous | ✅ |
| — | contract | No transport is bound — no `servers`, no `bindings` | ✅ |

60 assertions. Python suite: 492 → **552**.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-026` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 552 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | A second document; `openapi.yaml` untouched |
| R3 graph diff as expected | **PASS** | One YAML document, one test module |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-006, REQ-DATA-008 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Plus `tenant_id` required on every envelope |

**Overall:** **PASS**. Detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Eight events specified with envelope and guarantees
- [x] Payload schemas **structurally** exclude personal data — closed objects, scanned by test, with the scan itself meta-tested
- [x] Ordering documented and scoped to per-trip — **and honest about the two events that are not about a trip**

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. One mypy annotation — the first sub-step in several where the contract did not catch me out |
| Notes / surprises | **The "no content in payloads" rule is a tenancy control, and I had been reading it as privacy tidiness.** An event is consumed by services that never authenticated the user who caused it — `EVT-001` alone reaches evidence assembly, the knowledge graph and analytics. A payload carrying constraint values hands all three data nobody checked they may see, and the check cannot be retrofitted because the data is already in the log and in every replica. `EVT-001` therefore carries four integers where the constraints would be.<br><br>**`exactly-once-effect`, not `exactly-once`.** No transport delivers exactly once; anything claiming to is deduplicating somewhere and calling it a guarantee. The contract names the consumer's obligation instead of implying the transport absorbs it — this is the guarantee most often written down wrongly, so a test asserts the description says so.<br><br>Two events are deliberately not keyed by `trip_id`. Keying a deletion request or provider health that way would look consistent and be wrong, and the failure would be a rare load-dependent ordering bug rather than anything obvious.<br><br>**One sub-step ran nearly clean, and the reason is instructive.** `.02` and `.03` each found several defects because they were reconciling two documents that had drifted. `.05` had one complete register to work from — `EVENT_CONTRACTS.md` lists all eight events with payload, delivery, retention and replay — and produced one trivial annotation error. The quality of the source document is what determined the number of defects, not the care taken. |
