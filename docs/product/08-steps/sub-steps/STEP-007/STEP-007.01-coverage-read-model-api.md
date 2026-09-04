---
sub_step_id: STEP-007.01
parent_step: STEP-007
title: Coverage read model and the public coverage API
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-002, REQ-EVID-006]
blast_radius_id: BR-059
depends_on: [STEP-006.09]
last_updated: 2026-09-04
---

# STEP-007.01 — Coverage read model and the public coverage API

## 1. Outcome
`API-017` serves the coverage read model STEP-006.09 already builds, and the response names no supplier.

## 2. Scope and boundary
**In scope:** The `GET /coverage` handler; wiring `coverage_read_model` to `Coverage`; the first FastAPI route that serves a product operation.

**Not in this sub-step:** The public page (`.02`); degradation disclosure wiring (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-002, REQ-EVID-006 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED**; `RISK-017` for the two migrations |
| HEAD / indexed commit | `64c209d` — matched HEAD at pre-change |
| Queries run | `impact` on `coverage_projection`, `PublicCoverage`, `Projection`, `UnitOfWork`, grep cross-checked |
| **Finding** | `coverage_projection` returned **14 dependants against 18 real** — the first non-trivial answer the graph has given. `UnitOfWork` still reported 0 against 17, so `RISK-016` is narrowing where a symbol has many same-language callers and unchanged where it does not |
| Unknown / low-confidence areas | Resolved during execution: this was the first product route, and it found three defects in `VERIFIED` work — `BUG-028`, `BUG-029`, `BUG-030` |
| Blast radius | **[BR-059](../../../10-logs/blast-radius/BR-059-coverage-api.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Handler validated against the contract's `Coverage` schema in a test, resolved from the document root so internal `$ref`s work
- [x] ~~Reads through a tenant-bound unit of work~~ — **this plan item was wrong.** `API-017` is `security: []`, so there is no tenant to bind; `UnitOfWork` refuses without one, correctly. Using it here would have meant inventing a tenant for a public request, and an invented tenant is one somebody later trusts. `BUG-028`
- [x] **One aggregate health value** — never a list, never a count, never a supplier name, enforced in the projection, the table and the handler
- [x] ~~Cache key includes the tenant~~ — **also wrong, for the same reason.** The cache holds one public document with no tenant, so the property tested is *"nothing scoped is in here"* rather than *"the key is scoped"*. The `[cache]` R7 vector was **narrowed, not closed**
- [x] Contract compatibility passes; **no contract change was needed** — the implementation moved to fit it

## 6. Contracts and schema changes
Implements `API-017` as declared. **No contract change is expected**, and one would be a finding: the contract was written first precisely so the handler discovers nothing new. If it does, that is `CONTRACT_CHANGE_POLICY` work and a blast-radius record of its own.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-TRIP-002 | contract | The response validates against the committed `Coverage` schema |
| — | security | No provider name, count or quota appears in any response field |
| — | security | **A row is visible with no tenant context** — `BUG-028`'s regression test |
| — | security | The table has no tenant column and does not force RLS |
| — | security | **Nothing tenant-scoped is in the cache**, asserted on the value and every key it has held |
| — | unit | An empty read model reports `unavailable`, not `healthy` |
| — | unit | The cache expires, so degradation reaches the traveller (`REQ-EVID-006`) |
| — | unit | The TTL is short enough to be a disclosure bound — asserted, not assumed |
| — | unit | `display_name` is not the region id; `date_bounds` come from the row |
| — | integration | **The handler's own query returns the row with no tenant bound** |
| — | integration | A region must have a name; date bounds cannot end before they start |

22 tests. **Mutation testing: 13 seeded, 13 killed.**

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Traces carry a tenant-safe correlation ID. **`REQ-SEC-002`'s cache vector becomes testable here** — `test_pending_vector_is_still_absent[cache]` will fire the moment a cache appears, exactly as the outbox placeholder did at STEP-006.06, and a real isolation test is then owed.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit; the route disappears and the read model is untouched. No migration.

## 12. Acceptance criteria
- [x] `getCoverage` returns the read model, validated against the contract
- [x] No supplier identity, count or quota is reachable through the response
- [x] ~~The cache key is tenant-scoped~~ — **superseded.** The endpoint is public; the property is that nothing tenant-scoped is cached, and it is tested
- [x] A region absent from the read model reads as uncovered, and an empty model as `unavailable`

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-04 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **13 of 13 killed** — 9 of 13 before the four gaps were closed |
| Bugs found | **`BUG-028`, `BUG-029`, `BUG-030`** — all three in work already marked `VERIFIED` |
| Notes / surprises | **Two of this record's own plan items were wrong, and the contract is what said so.** I wrote "reads through a tenant-bound unit of work" and "cache key includes the tenant" before reading that `API-017` is `security: []`. A public operation has no tenant; `UnitOfWork` correctly refuses without one. Both items are struck through rather than deleted, because the correction is the useful part.<br><br>**`BUG-028` is the serious one.** The read model was tenant-scoped and the endpoint that exists to serve it is public, so RLS denied every row — and the endpoint does not error, it returns "we support nowhere" to the person deciding whether to sign up. The same shape as `BUG-027`: writing the next sub-step is how the last one's defect is found.<br><br>**A guard I wrote caught me one step later.** `platform/` shadows the stdlib and `apps/api/src` is on `pythonpath`. I caught it by importing before writing the handler, wrote the guard with a seeded-violation meta-test, wired it into `verify` — and it failed immediately on `tests/platform`, which I had just created.<br><br>**And the honesty failure.** Running the meta-suite to check that new guard revealed it had never run: twenty regression entries claimed "meta-suite 72/72", the real total is 74, and three were failing — about `BUG-023`'s exact class. `guard:meta` is now in `verify`. What caught it was not diligence but an unrelated accident, which is the least comfortable and most useful thing in this record. |
