---
sub_step_id: STEP-005.08
parent_step: STEP-005
title: Field-specific freshness policy and expiry
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-005, REQ-EVID-005]
blast_radius_id: BR-047
depends_on: [STEP-005.07]
last_updated: 2026-08-18
---

# STEP-005.08 — Field-specific freshness policy and expiry

## 1. Outcome
Each field class carries its own expiry, so closures expire in minutes while descriptions expire in weeks, and staleness is computed at time of use.

## 2. Scope and boundary
**In scope:** `services/ingestion/src/freshness.py`; field-class registry; age-at-use computation; staleness marking.

**Not in this sub-step:** Evidence-pack assembly ([STEP-010](../../STEP-010-destination-evidence-assembly.md)); UI display of staleness.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-005, REQ-EVID-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `a7a5a04` — matched HEAD at pre-change |
| Queries run | `impact` on `Provenance`, `CanonicalPlace`, `ResumableRun`, `CircuitBreaker` (upstream, depth 3, `--include-tests`), each cross-checked against grep per `RISK-016` |
| **Finding** | `RISK-016` reproduced a third time — 0–1 dependants reported against 11–12 real call sites |
| Unknown / low-confidence areas | Threshold values per class need product sign-off (`DEC-005`). **Their ordering does not** — `REQ-DATA-005` states it, so it is asserted as an invariant |
| Blast radius | **[BR-047](../../../10-logs/blast-radius/BR-047-freshness-policy.md)** — LOW, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Field-class registry — disruption 5 min, hours 6 h, price 7 days, description 90 days, each with a written rationale and **no default for an unregistered class**
- [x] **Age-at-use computed against observed time, not ingestion time.** Both are carried so the choice is provable; `ingestion_lag` publishes the difference
- [x] **Effective-window check separate from freshness**, and checked *first* — a fresh fact about the wrong dates is not fixed by re-fetching
- [x] Staleness computed at use and **never stored** — a stored boolean is wrong as soon as the clock moves
- [x] Critical-field staleness blocks the option; advisory staleness marks it and publishes `staleness_ratio`

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-005 | unit | Each field class expires per its own threshold — one day old is expired hours and a good description |
| TST-EVID-005 | unit | Stale hours block the option; a stale price is marked and does not |
| — | unit | Fresh observation with a non-covering effective window is a coverage gap |
| — | unit | **A freshly fetched stale value is stale** — the central rule |
| — | unit | Partial cover does not describe the uncovered days |
| — | unit | An open-ended window is not an expired one |
| — | unit | Applicability is reported before staleness when both fail |
| — | invariant | `REQ-DATA-005`'s ordering holds over the registry, whatever `DEC-005` decides |
| — | unit | A future-dated observation is refused, not treated as maximally fresh |
| — | unit | Exactly at the threshold is fresh; one microsecond past is not |
| — | structural | No stored staleness flag and no confidence constant |

26 tests. **Mutation testing: 10 seeded, 10 killed** — the tenth only after the
boundary decision was made explicit.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-037` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 1011 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One new module, one new test module |
| R4 untested requirements | **PASS — improved** | REQ-DATA-005 and REQ-EVID-005 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…027; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Each field class expires per its own threshold
- [x] Age computed from observation, not ingestion
- [x] Applicability checked independently of freshness
- [x] Critical staleness blocks; advisory staleness marks
- [x] No default policy for an unregistered field class

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-18 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **10 of 10 killed** — 9 of 10 before the boundary test existed |
| Bugs found | None |
| Notes / surprises | **A provisional constant can still be tested.** `DEC-005` has not signed off the four thresholds, and after `BUG-026` the instinct was to treat any unsigned number as untestable. But `REQ-DATA-005` does not state a value — it states an **ordering**: hours and disruptions expire faster than descriptive content. That is a property of the table, it is the requirement itself, and it survives whatever `DEC-005` decides. Test the property the requirement states, not the number somebody picked.<br><br>**The surviving mutant was a decision nobody had made.** Nine died at once; the tenth flipped `<=` to `<` at exactly the threshold, and no test covered that instant. Inclusive is right — "expires after six hours" should not expire *at* six hours, and an exclusive bound makes the verdict depend on clock resolution. The gap was a missing decision more than a missing assertion.<br><br>**The module refuses to compute a confidence penalty**, and that is scope discipline rather than incompleteness. `REQ-EVID-005` allows blocking or lowering confidence; blocking follows from the field class and is decided here, while the confidence *curve* belongs to the scenario scorer. A multiplier invented here would be `BUG-026` in a different module. |
