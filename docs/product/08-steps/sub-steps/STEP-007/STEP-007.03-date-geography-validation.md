---
sub_step_id: STEP-007.03
parent_step: STEP-007
title: Date and geography validation with honest refusal states
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-001, REQ-TRIP-002]
blast_radius_id: BR-061
depends_on: [STEP-007.02]
last_updated: 2026-09-05
---

# STEP-007.03 — Date and geography validation with honest refusal states

## 1. Outcome
A request outside coverage is refused with an explanation and produces no partial simulation.

## 2. Scope and boundary
**In scope:** Date-range and destination validation; the refusal surface; `CoverageModel.assess` wired to the UI.

**Not in this sub-step:** Brief capture (`STEP-009`); waitlist (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-001, REQ-TRIP-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `7adead2` — matched HEAD at pre-change |
| Queries run | `impact` upstream on `read_coverage`, `CoverageModel.assess`, `get_coverage`; `context` on the handler; `api_impact`; `check({cycles})`; three Cypher queries over the edge table. **Each cross-checked against grep** |
| **`RISK-016` #13 — and the worst one yet** | `impact(get_coverage, upstream)` returned **0, LOW, `"epistemic": "exact"`**; grep found `app.py:126`. Cause, measured: `apps/api/src/app.py` has **no outgoing edges at all** and the `/coverage` handler is an island node, while cross-file Python `CALLS` resolve 450 times elsewhere. Every impact query on anything the API application consumes under-reports by exactly the API application — the only deployable HTTP surface there is. [BR-061](../../../10-logs/blast-radius/BR-061-date-geography-validation.md) §2 |
| Migration present? | **Yes — `018`.** `RISK-017` applies; blast radius from reading it and from mutation against the **deployed** schema |
| Unknown / low-confidence areas | Trip length. Resolved as **`DEC-011`**: 3–7 enforced as `PRODUCT_SCOPE` declares, with a recorded recommendation that the *lower* bound is probably wrong. `ASM-015`'s reasoning constrains the upper bound only |
| Blast radius | **[BR-061](../../../10-logs/blast-radius/BR-061-date-geography-validation.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | **Yes** — a contract addition, and `DEC-011` ships a bound I recommended against |

## 5. Implementation plan
- [x] Dates validated in the destination's zone via `domain.temporal.zone_of` — **not the browser's, and not the server's**. `018` adds `time_zone` NOT NULL with no default; an unknown zone is refused, never defaulted to UTC
- [x] Refusals rendered with their reason. **A new type, not `TripRefused`** — `PlanningRefused` carries a registered `code` so §17's "refusal rate by reason" is countable; extending a frozen `VERIFIED` dataclass to serve a consumer it does not have was the wrong direction of fit ([BR-061](../../../10-logs/blast-radius/BR-061-date-geography-validation.md) §6)
- [x] **No partial result path** — asserted three ways: neither type has a field a plan could occupy, the module imports nothing that could build one, and the page renders no table on a refusal
- [x] Degraded coverage accepted with its disclosure. **This is `BUG-034`** — four documents said otherwise, and the word "degraded" turned out to mean two things
- [x] Refusals announced **assertively**, acceptances **politely**, asserted on the live regions themselves

## 6. Contracts and schema changes
Consumes `API-017`. Trip creation is `STEP-008.06`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-TRIP-002 | integration | An out-of-coverage request is refused as a 422 problem document, with the reason and the supported bounds |
| — | unit + jsdom | **No partial simulation** — `TestNoPartialSimulation`, `TestNoPartialSimulationOverHttp`, and `nothing plan-shaped is rendered on a refusal` |
| — | unit | Dates validate in the destination zone. Written **across the date line**, where the destination's answer and the server's differ — with a negative control declaring the same region in UTC, which accepts |
| — | unit | A four-day trip spanning the 25-hour Zurich DST day is still four days |
| — | jsdom | The refusal lands in the **assertive** region and the acceptance does not |
| — | unit + integration | A degraded region is accepted with a disclosure; a stale or suspended one is refused |
| — | browser | While nothing is declared, no form is offered — and the page says why |

**Mutation testing: 20 mutants, 20 killed, 0 survivors.** Each rule this sub-step
claims has a seeded defect. The two that matter most: mutant #1 replaces the
destination's date with the server's and is killed by a date-line test; mutant #9
collapses `stale` and `degraded` into one refusal — `BUG-034` made real — and is
killed by the disclosure test.

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Refusal reasons are logged without the destination string until consent, since a destination plus a timestamp is close to a travel plan.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | **1373 Python** (from 1313) + **71 web** (from 63) + 307 UI + **58 browser** (from 56) |
| R2 contract compatibility | **PASS — additive** | Gate reports `[ADDITIVE] POST /coverage:check — new operation`. Clients regenerated |
| R3 graph diff as expected | **PASS** | One new module, one new route, one new page component, one migration, three guards amended |
| R4 untested requirements | **PASS — improved** | REQ-TRIP-001 and REQ-TRIP-002 gain their first behavioural coverage |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…034; **guard meta-suite 76/76**, run on the pinned Node |
| R7 tenant isolation | **PASS — 18/18** | `read_region` binds no tenant and is asserted to name none; the operation is public and coverage is global (`BUG-028`) |

**Overall:** **PASS**.

## 11. Rollback
Revert the commit; `.02` remains a read-only page.

## 12. Acceptance criteria
- [x] Out-of-coverage refused with an explanation, as an RFC 9457 problem document
- [x] No partial simulation on any refusal path — asserted structurally at the type, the module and the page
- [x] Dates validated in the destination's zone, across the date line and across a DST boundary
- [x] Refusals announced assertively; acceptances politely

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-05 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **20 seeded, 20 killed, 0 survivors** |
| Bugs found | **BUG-034** (terminology collision in four documents, one a contract). Three of my own, caught by gates rather than by reading — see below |
| Notes / surprises | **The hazard this record predicted was real, and it was not where the record put it.** The prediction was the *browser's* zone. The actual trap is that there are three candidate clocks — browser, server, destination — and only the third is correct, so a server-side implementation looks safe while being wrong for every caller whose day differs from the server's. `_today_in` takes `now` as a required argument with no default for exactly that reason: a function that reaches for the wall clock cannot be tested across the boundary it exists to handle. Every zone test is written across the date line, with a negative control declaring the same region in UTC.<br><br>**I wrote a blast-radius section, then found it was wrong, then fixed it before implementing.** `BR-061` §3 originally concluded that four documents contradicted `VERIFIED` code and the prose was wrong. Reading `ERROR_MODEL.md` properly showed the conflict was terminological: `coverage.provider_degraded` means *health insufficient for reliable planning*, which is `UNAVAILABLE`, not the enum member spelled `DEGRADED`. The structural proof is that there is no `coverage.provider_unavailable` — under the other reading, the requirement's own refusal path would be uncodeable. Logged as `BUG-034`, fixed as prose. It is a real defect: `PUBLICATION[RECOVERING] is DEGRADED`, so an implementer following §9 literally makes every provider recovery a total outage.<br><br>**Three of my own defects, each caught by a gate rather than by review.** (1) `Problem.remediation` requires `kind` and none of my refusals had one — found by the schema test; now enforced at the type. (2) Setting `environment: 'jsdom'` for the whole web package broke `i18n.test.ts`, which reads its own source through `import.meta.url` to prove a **security** property — a config default had switched off a security test while looking like configuration. Fixed with a per-file `@vitest-environment`. (3) `[aria-live="polite"]` is not unique on a page with a form: every `Field` renders its own empty error slot, so the first match was a field's, and the test reported an acceptance had not been announced when it had.<br><br>**Two guards fired and both were right.** A second `security: []` operation, and a POST with no `Idempotency-Key`. The second is the interesting one — the POST changes nothing, and it is a POST rather than a GET because a destination plus dates in a query string lands in access logs, proxy logs and browser history on a page that promises nothing identifies the visitor. The exemption is declared in the **contract** as `x-journeylab-safe` and the gate reads it; an allowlist of operation ids in the test would have grown silently. Two new tests check the claim rather than trusting it, and the rule now has one definition instead of two copies.<br><br>**A refusal is a problem document, not a 200 with a `refused` field, and I designed it the wrong way first.** The register had already decided, with statuses. The argument that settled it is `BUG-032`: three tests passed against a 404 because they asserted absence, and a success body that must be inspected to discover it is a rejection has the same shape. A 422 cannot be misread. The distinction between *the answer is no* and *we could not ask* is carried by the code and `retryable`, not by the status. |
