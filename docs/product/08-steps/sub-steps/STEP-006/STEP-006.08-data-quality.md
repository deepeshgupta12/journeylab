---
sub_step_id: STEP-006.08
parent_step: STEP-006
title: Data-quality expectations and quarantine
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-005, REQ-DATA-002]
blast_radius_id: BR-057
depends_on: [STEP-006.07]
last_updated: 2026-09-03
---

# STEP-006.08 — Data-quality expectations and quarantine

## 1. Outcome
Executable expectations run against every ingestion batch, and failing data is quarantined rather than silently entering planning.

## 2. Scope and boundary
**In scope:** `data/quality/domain_expectations.yml`; expectation runner; quarantine store; alerting.

**Not in this sub-step:** Provider reconciliation (`STEP-005.09`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-005, REQ-DATA-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** for the module; **`RISK-017`** for the migration |
| HEAD / indexed commit | `7299ef1` — matched HEAD at pre-change |
| Queries run | `impact` on `Envelope`, `Relay`, `Status`, `OutboxRow`, grep cross-checked (`RISK-016`) |
| Unknown / low-confidence areas | No baseline corpus exists, so drift reports `UNAVAILABLE` rather than passing. `DRIFT_SIGMA` provisional pending `DEC-005` |
| Blast radius | **[BR-057](../../../10-logs/blast-radius/BR-057-data-quality.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] All six classes declared in `data/quality/domain_expectations.yml` and implemented — **a declared class with no implementation raises**, because the YAML is the specification a curator reads
- [x] **Referential integrity is a block, not a severity** — refused in code *and* by a database constraint, so it survives a second writer
- [x] Failing batch quarantined with the failure reason; a result with no detail is refused
- [x] **Quarantine written to `quarantined_batches`**, which a curator can query — see §6a
- [x] Drift measured in standard deviations against a recorded baseline — see §6

## 6. Two defects external review found that this suite did not

Recorded in full, because the useful part is why the tests missed them.

**Drift reported a pass without measuring drift.** `_distribution_drift` returned
`PASSED` whenever a `baseline_mean` field was merely present. The one check whose
entire job is noticing a distribution move could not notice one — inside a module
whose docstring opens with *"a suite that ran nothing must not report a pass"*.

Every test asserted the verdict for a single input, and none asserted that a
**drifted** batch produced a different one. Fourteen mutants passed over it, because a
mutant proves a test notices a change and cannot notice a function that was already
inert. Fixing it broke the "clean batch" test, whose fixture had a baseline and no
observation — it had been passing on exactly the vacuousness that hid the defect.

Drift is now measured in **standard deviations**, not percent: a 10% move in price and
a 10% move in duration are not comparably surprising, and a percentage threshold has
to be retuned per field. A baseline with zero spread reports `UNAVAILABLE`, since any
non-zero move is infinitely many sigma and would quarantine everything.

## 6a. The quarantine reached nobody

§5 requires quarantine *"visible to curators, not just logged"*. `Quarantine` held
entries in a list that lived for the duration of one batch run, and the
`quarantined_batches` table was never written to. Every test passed, because every
test exercised the class.

Now behind a `QuarantineStore` port with a PostgreSQL implementation.
`Quarantine.persisted` reports `False` when a batch was held with no store — not an
exception, since a runner without one is a legitimate test configuration, but the
caller must know that nothing reached anybody.

## 6b. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-005 | unit | Each expectation catches its seeded violation |
| TST-NFR-012 | unit | An unresolved location **blocks** rather than warns |
| — | unit | A curator cannot release a block; a released block cannot be constructed |
| — | integration | **The database refuses a blocking release too** — the layer a second writer bypasses |
| — | unit | **A drifted batch fails and a steady one passes**; a sub-threshold shift passes |
| — | unit | A baseline with no spread cannot judge a shift |
| — | integration | **A held batch is readable from the database** |
| — | unit | Holding with no store reports that nothing was persisted |
| — | unit | Every declared expectation has an implementation; an unimplemented one raises |
| — | unit | Drift and completeness report `UNAVAILABLE`, which neither quarantines nor admits |

27 tests. **Mutation testing: 14 seeded, 14 killed.**

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-047` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] All six expectation classes implemented, and a declared-but-missing one raises
- [x] Seeded violations caught — **including a drifted distribution**, which the first version could not detect
- [x] Quarantine visible and actionable, **in the database**
- [x] Unresolved locations hard-blocked, in code and at the table

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-03 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **14 of 14 killed** — 12 of 14 before the database constraints had tests |
| Bugs found | **Two of mine, both found by external review rather than by this suite** |
| Notes / surprises | **I wrote the failure I was warning about, in the module warning about it.** The drift check returned `PASSED` whenever a baseline field existed, measuring nothing — inside a module whose docstring opens with "a suite that ran nothing must not report a pass". The distance between stating a principle and applying it is apparently not zero even when the statement is three paragraphs above the code.<br><br>**Mutation testing could not have found either defect, and that is the useful limit to record.** A mutant proves a test notices a *change*; it cannot notice a function that was already inert, or a persistence path that was never exercised. Both survivors it *did* find were database constraints with no test behind them — the same blind spot from the other end. Finding these needed a reader asking what the code actually does.<br><br>**The mutation restore failed exactly as it did in `.01`** — a mutant that permits a write leaves rows that trip the constraint's own re-creation. I recorded that lesson in `BR-050` §7 five sub-steps ago and did not carry it into this harness. A lesson written down is not a lesson applied.<br><br>**Block and quarantine are different affordances, not different severities.** Modelled as severities, the UI grows one release button, somebody uses it, and `REQ-NFR-012`'s hard block becomes a strongly-worded warning. Refused in code and at the database, deliberately twice. |
