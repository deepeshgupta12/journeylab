---
sub_step_id: STEP-005.04
parent_step: STEP-005
title: Transit routes, schedules and service alerts adapter
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-NFR-011]
blast_radius_id: BR-043
depends_on: [STEP-005.03]
last_updated: 2026-08-17
---

# STEP-005.04 — Transit routes, schedules and service alerts adapter

## 1. Outcome
Transit routes, schedules and service alerts are ingested with correct time-zone normalization and minute-level alert freshness.

## 2. Scope and boundary
**In scope:** `services/integrations/src/transit/`; GTFS-style feed handling; service calendars; alert stream; feed version pinning.

**Not in this sub-step:** Travel-matrix computation (`.05`); live impact matching ([STEP-018](../../STEP-018-condition-monitoring.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-NFR-011 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `bb84631` — matched HEAD at pre-change |
| Queries run | `cypher` over `services/integrations/src/transit` — 0 nodes, additive; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **Alert latency remains unverified** — no live fetch has been made against `opentransportdata.swiss`, so the 5-minute SLO is a promise this code enforces rather than one the provider is known to meet. The SLO is a **parameter** for that reason. Also unverified: real feed field names, the same gap `.02` and `.03` carry, which `.07` meets |
| Blast radius | **[BR-043](../../../10-logs/blast-radius/BR-043-transit-adapter.md) — MEDIUM, confidence HIGH.** The record predicted `BR-033`, which STEP-004.06 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Feed pinned by **content hash**, not the operator's version string — a republication that keeps its label and changes its contents is exactly what a version string cannot catch
- [x] Service calendars with exceptions, where **an exception always wins**; `runs_on` returns immediately so the weekly pattern is unreachable afterwards
- [x] Stop resolution with **no nearest-match**; an unresolvable stop returns `None` and records a `CoverageGap`
- [x] **Service time, not calendar time.** `25:30` resolves onto the following day; the day is anchored per the GTFS noon-minus-twelve rule (§ BR-043 §8 on what that does and does not buy)
- [x] Alerts with validity windows and staleness measured from **observation**, not onset
- [x] `TransitUnavailable` requires a disclosure naming the modes still available

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-002 | integration | Feed version pinned; drift rejected |
| TST-NFR-011 | integration | Alert freshness meets the documented SLO |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) `IMPL-040` · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · BUG_REGISTER n/a — no bug found
- [x] `BR-043`
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 843 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One package into `services/integrations/` |
| R4 untested requirements | **PASS — improved** | REQ-DATA-002's feed-version clause and REQ-NFR-011 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…025; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Feed version pinned and drift detected
- [ ] Service calendars correct including exceptions
- [ ] Unresolvable stops become coverage gaps
- [ ] Transit unavailability disclosed rather than silently substituted

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-17 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. One **untested claim of my own**, corrected — see below |
| Notes / surprises | **A service day is not a calendar day**, and both naive readings of GTFS's `25:30` are wrong in opposite directions. Rejecting it deletes the night network and the gap reads as "no service"; wrapping it to 01:30 today moves every late departure back twenty-four hours, which is a train that already left (`REQ-CONS-004`, S1). `ServiceTime` is deliberately not a `datetime.time` because `25:30` is not representable as one.<br><br>**The calendar precedence failure is asymmetric, so the code is too.** Ignoring a removal strands somebody at a station on Christmas Day; ignoring an addition merely makes the plan worse. Exceptions are consulted first and return immediately, so the weekly pattern is unreachable after an explicit date has spoken.<br><br>**A mutant survived and it deserved to, which is the finding worth keeping.** Swapping the GTFS noon-minus-twelve anchor for a plain wall-clock midnight did not fail the suite. I went looking for the spring-forward case the anchor supposedly prevents — both 2026 Zurich transitions plus Havana, Santiago, Beirut and Asunción — and the two anchors gave the **identical instant every time**, because Python's `zoneinfo` normalises rather than raising. My docstring had claimed the anchor prevents a defect; it now says it is specification conformance, records the failed attempt, and points at the test pinning the equivalence. **Reported as 7 of 8 killed, not 8 of 8** — a survivor quietly reclassified is how a mutation score becomes decorative.<br><br>**Three sub-steps, one discipline.** `.02`: unknown hours are not closed. `.03`: a normal is not a forecast. `.04`: a service day is not a calendar day, and beyond the feed range is not "does not run". Every wrong answer in this family is a coherent, cited, confidently wrong plan rather than a crash. |
