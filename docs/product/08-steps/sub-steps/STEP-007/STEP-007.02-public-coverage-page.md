---
sub_step_id: STEP-007.02
parent_step: STEP-007
title: Public coverage page with limitations and privacy summary
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-002, REQ-A11Y-001, REQ-A11Y-002]
blast_radius_id: BR-060
depends_on: [STEP-007.01]
last_updated: 2026-09-04
---

# STEP-007.02 — Public coverage page with limitations and privacy summary

## 1. Outcome
A traveller can see, before signing up, which regions are supported and what the honest limitations are.

## 2. Scope and boundary
**In scope:** The `/coverage` page; region list; limitations rendering; the privacy summary; CSV export of the region table.

**Not in this sub-step:** Date validation (`.03`); waitlist (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-002, REQ-A11Y-001, REQ-A11Y-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `5d3cd5b` — matched HEAD at pre-change |
| Queries run | `impact` on `DataTable`, `toCsv`, `getCoverage`, grep cross-checked |
| **Finding** | `getCoverage` returned `UNKNOWN` — the graph holds the Python and TypeScript definitions separately and neither imports the other. **The call it cannot see is the HTTP one**, which is this sub-step's whole subject: the graph describes imports, not systems |
| Unknown / low-confidence areas | Resolved during execution: the page needed a server, which made the ASGI app a precondition rather than scope creep |
| Blast radius | **[BR-060](../../../10-logs/blast-radius/BR-060-coverage-page.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | **Yes, and obtained.** The reserved port block was full; the owner approved extending it to 5710. A real second party this time, because the constraint is about a machine I cannot inspect |

## 5. Implementation plan
- [x] Region table as the primary surface. **There is no map to disable** — a stronger statement than `REQ-A11Y-003` asks for, and available only because the table was built first
- [x] Limitations rendered verbatim, as a list, never summarised into a cell
- [x] CSV export — from `DataTable`, which already exports what it is sorted by. A second exporter here would disagree with the table the first time a column changed
- [x] Privacy summary stating the guest path, on a page that reads no session and **sets no cookie at all**
- [x] Freshness marked as **text**, not colour — WCAG 1.4.1, and a screen reader gets the same word a sighted reader sees
- [x] **Plus the ASGI application the page reads from** — a precondition, see §6

## 6. The page needed a server

`.01` built the handler and nothing routed to it. Two ways to get data onto a page:

| | Consequence |
| --- | --- |
| Query Postgres from Next.js | Breaks `ADR-003` (one deployable API application), already forbidden in spirit by `module-boundaries.sh`, and duplicates the aggregate-health rule `REQ-EVID-006` depends on in a second language — how `BUG-029` happened |
| Serve it over HTTP | The architecture as declared |

So `apps/api/src/app.py` is a **precondition**, like `BUG-027`'s fix was for entity
resolution. One route, one dependency, no middleware this sub-step does not need.

**`problem()` refused to invent an error code.** No registered code covered a
dependency outage, and the builder rejects unknown ones by design. The honest fix was
the long one: add the row to `ERROR_MODEL.md`, regenerate the registry, the JSON
schema and the TypeScript client, and run the compatibility gate. Reaching for
`coverage.provider_degraded` would have been faster and would have told a client the
wrong thing about what failed.

## 6a. Contracts and schema changes
Consumes `API-017`. No change.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-002 | axe | Zero WCAG 2.2 AA violations across two device profiles |
| TST-TRIP-002 | browser | **The empty state says "no region has been declared yet"** — not an empty table, which would read as "we support nowhere" |
| — | browser | **No cookie is set at all** (`REQ-PRIV-001`) |
| — | browser | No supplier name appears anywhere in the DOM |
| — | browser | **There is no map to disable** |
| — | browser | The CSV control is present; the privacy summary precedes any request for an account |
| — | browser | The page is keyboard reachable |
| — | integration | The API serves the contract's `Coverage` schema, unauthenticated |
| — | integration | A declared region reaches the response with its dates and limitations, and **without `accepting_trips`** |
| — | integration | **A database failure is a 503 problem document that leaks no DSN** — asserted with a password in it |
| — | structural | The health check does not touch the database |

56 browser tests (up from 40) and 10 API tests. **Mutation testing: 7 seeded, 7
killed.**

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
No PII. The page is reachable without a session, so it must not set a tenant-scoped cookie before consent (`REQ-PRIV-001`).

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
Revert the commit. The page is additive and nothing links to it until `.03`.

## 12. Acceptance criteria
- [x] Regions and limitations visible without an account
- [x] Completable with the map disabled — **there is no map**
- [x] CSV export available from the table
- [x] axe clean in both device profiles

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-04 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **7 of 7 killed** |
| Bugs found | None new. Two guards corrected — see below |
| Owner decision | Port block extended to **5710** |
| Notes / surprises | **The owner had to be asked, and it was the right call.** The reserved block was full, and `port-collisions.sh` exists because *"5544 looked free to `lsof` only because Saakshya was stopped"*. Picking 5710 because it looked free would have been that exact mistake, on a machine I cannot inspect.<br><br>**A guard broke on something it had never been wrong about.** `readme-accuracy.sh` asserted every `\| 570X \|` row was published by compose — true while the only such table listed containers. An application-ports table made all three rows look like missing containers. The guard's subject was inferred from a number rather than stated; it now reads between explicit markers, and widening its range from `570[0-9]` to `5[0-9]{3}` also closed a hole where a documented port outside the block escaped checking entirely.<br><br>**The accessibility run now depends on the API process**, deliberately: a coverage page rendered against no data would pass axe and prove nothing about the surface being shipped.<br><br>**TypeScript found a contract detail I had coded past.** `limitations` is optional in `CoverageRegion`, so a region may omit it rather than send `[]`. The handler always sends one, and coding to that would have made the page correct only against today's server. |
