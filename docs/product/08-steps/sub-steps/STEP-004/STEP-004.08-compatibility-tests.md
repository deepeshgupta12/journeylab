---
sub_step_id: STEP-004.08
parent_step: STEP-004
title: Backward-compatibility and consumer contract tests
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-008]
blast_radius_id: BR-035
depends_on: [STEP-004.07]
last_updated: 2026-08-12
---

# STEP-004.08 — Backward-compatibility and consumer contract tests

## 1. Outcome
A breaking contract change fails CI unless it carries a new major version, migration guide, consumer notice and sunset date.

## 2. Scope and boundary
**In scope:** `tests/contracts/`; OpenAPI/AsyncAPI diff against the previous release; consumer-driven contract tests; deprecation metadata checks.

**Not in this sub-step:** Provider integration contract tests ([STEP-005](../../STEP-005-source-integrations-and-ingestion.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `eb30a26` — indexed commit matched HEAD at pre-change |
| Queries run | `impact(generate_typescript, upstream, includeTests)` — 1 direct, LOW, `epistemic: exact`; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **Semantic change remains undetectable** and is now stated in three places rather than one: the classifier's docstring, `BASELINE.md` §4 and `ENH-001`. **AsyncAPI is not diffed** — `DEC-009` is open (§9 of BR-035) |
| Blast radius | **[BR-035](../../../10-logs/blast-radius/BR-035-compatibility-tests.md) — MEDIUM, confidence HIGH.** The record predicted `BR-029`, which STEP-004.02 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Diff current contracts against the last released version — `contracts/baseline/`, a committed snapshot; **there is no release, and BASELINE.md §2 says so**
- [x] Classify diffs: additive / potentially breaking / breaking — `tools/contract_diff.py`, **direction-aware**
- [x] **Breaking diff without a version bump fails the build** — `tools/check_compatibility.py`
- [x] Deprecated operation without a `Sunset` date fails the build — both `Sunset` and `Deprecation` required
- [x] Consumer-driven contract test harness — built, with the docstring stating plainly that **no external consumer exists**
- [x] **Meta-test: a seeded breaking change must fail CI** — 8 seeds, including the bypass and the must-pass case

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-008 | Guard meta | Breaking change without a major bump fails — **4 seeds killed** |
| TST-PLAT-008b | Guard meta | The same change WITH a major bump passes — **the case that proves the gate is not merely alarmed** |
| TST-PLAT-008c | Guard meta | A silently moved baseline fails — **the bypass** |
| TST-PLAT-008d | Guard meta | A deprecation with no `Sunset` fails |
| `test_contract_compatibility.py` | Unit | 57 assertions, half of them **direction pairs** asserting opposite severities for the same edit |
| `test_consumer_contracts.py` | Unit | Every known consumer's expectations, each with a recorded rationale |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) IMPL-032 · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) BUG-021
- [x] [ENHANCEMENT_LOG](../../../10-logs/ENHANCEMENT_LOG.md) ENH-001 — **logged, not implemented; owner decision pending**
- [x] `BR-035` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)
- [x] README — the contract-change workflow

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 648 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS — enforced, not judged** | Two response fields became required (BUG-021); the classifier built here rates that additive and the gate prints it. **First sub-step where R2 is a gate rather than an inspection** |
| R3 graph diff as expected | **PASS** | Two tools, one guard, one snapshot directory, three strengthened tests |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-008 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…021; meta-suite **55/55** |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Compatibility diff runs on every PR — in `pnpm verify`, therefore in CI
- [x] Breaking change blocked without the full policy — the **version bump** is gated; the gate names the §3 obligations it does *not* check rather than implying it checks them
- [x] Seeded breaking change proven to fail — 4 breaking seeds killed, plus the must-pass case
- [x] Deprecation metadata enforced — `Sunset` **and** `Deprecation`

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-12 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | **BUG-021** — two guarantees depended on fields that were optional. Found by the audit `.07` promised, not by ordinary work |
| Notes / surprises | **Direction decides the verdict, and that is the whole sub-step.** Request and response schemas have opposite compatibility rules — adding a required property breaks every client of a request and is harmless in a response; relaxing required-ness is a courtesy in one direction and a break in the other. Every rule inverts. So the classifier walks from the operations, records each schema's position, and applies the matching ruleset; a schema reachable from both takes the worse verdict. Half the tests are **pairs** asserting opposite severities for the same edit, because the two obvious wrong implementations — direction-blind, and alarmed-at-everything — each pass half of a conventional suite and neither survives a pair.<br><br>**The promised audit found two real defects in twenty minutes** that four sub-steps of ordinary work had missed. `JobEvent.sequence` was optional while its own description promised gap detection — and in a stream where some events carry a sequence and some do not, a missing number proves nothing, so optional sequencing does not weaken gap detection, it removes it while looking exactly like it is there. `model_versions` was optional while `solver_version` and `random_seed`, named in the same requirement, were required.<br><br>**I committed the same defect while auditing for it.** My orphan-schema test asserted `len(orphans) <= 2` and failed on three; raising it to 3 would have gone green and asserted nothing. Knowing the pattern by name did not stop me writing it, which is a better argument for the mechanical grep than any amount of care.<br><br>**My own tool lied to me once.** It classified a safe change correctly and then reported nothing, so tightening `JobEvent.required` produced "no differences from the baseline" about a contract I had just edited. Safe and absent are different answers and only one of them was true.<br><br>**The bypass is real and the fix is a speed bump, deliberately described as one.** Any compatibility gate falls to moving the baseline. A digest recorded in `BASELINE.md` makes that fail the build, but the author can edit both files — so what the check really does is turn a silent edit into a claimed release that did not happen. `BASELINE.md` §3 says that in those words rather than letting the next reader over-trust it.<br><br>**Two things are deliberately not done.** AsyncAPI is not diffed, because event compatibility turns on delivery semantics and `DEC-009` is open. Semantic change is not detected; `ENH-001` proposes catching the *documented* subset and is logged rather than built, because its real risk is teaching people to click through a warning — and this repository already has one degraded signal that reads like a real answer. |
