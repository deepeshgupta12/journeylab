---
sub_step_id: STEP-005.07
parent_step: STEP-005
title: Canonical place entity resolution and provider identifier graph
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-004]
blast_radius_id: BR-046
depends_on: [STEP-005.06]
last_updated: 2026-08-18
---

# STEP-005.07 — Canonical place entity resolution and provider identifier graph

## 1. Outcome
Multiple providers' views of the same venue converge into one canonical place, with
low-confidence matches routed to human review rather than merged.

## 2. Scope and boundary
**In scope:** `services/ingestion/src/entity_resolution.py`; matching by identifier
then geo+name similarity; provider identifier graph; review queue.

**Also delivered, because the sub-step could not be written without it:** the
`BUG-027` fix in `places/adapter.py`. Identifier-first matching over manufactured
identifiers is not identifier matching, and geo scoring needs a coordinate the
record did not carry.

**Not in this sub-step:** canonical persistence
([STEP-006](../../STEP-006-canonical-data-model-and-event-backbone.md)); a review
interface; blocking or indexing for corpus-scale comparison (§10).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-004 | Deduplicated into a canonical entity with a provider identifier graph | `TestAdapterOutputFeedsResolution`, `TestMergeIsReversible` |
| REQ-EVID-002 | Conflicting identifiers are surfaced, never resolved by proximity | `TestIdentifierEvidence` |
| REQ-CONS-006 | Entity identifiers and queue order are deterministic | `test_entity_ids_are_deterministic_rather_than_random` |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** — and **wrong**, see below |
| HEAD / indexed commit | `5eac52e` — matched HEAD at pre-change |
| Queries run | `impact` on `CanonicalPlace`, `adapt`, `Provenance` (upstream, depth 3, `--include-tests`); `context CanonicalPlace`; two `cypher` edge probes; a grep cross-check |
| **Finding** | The graph reported **0 dependants, LOW** for symbols with **11 live call sites**. Test modules are indexed but their cross-file edges are not. Logged as `RISK-016` |
| Unknown / low-confidence areas | Thresholds are measured against a hand-built sample, not a provider corpus. No provider fetch has been made |
| Blast radius | **[BR-046](../../../10-logs/blast-radius/BR-046-entity-resolution.md)** — MEDIUM, confidence **MEDIUM** |
| Approval required? | No |

## 5. Implementation plan
- [x] Exact match on shared provider identifiers first — restricted to namespaces
      that denote **at most one venue** (§7)
- [x] Geospatial proximity plus name similarity as a **secondary, gated** match —
      gated rather than scored, because compensation between signals is the
      false-merge mechanism
- [x] **Below-threshold matches go to a human review queue — never auto-merged.**
      There is no expiry, no default and no bulk approve, and a test asserts the
      queue's entire public surface
- [x] Provider identifier graph linking all source IDs to the canonical place
- [x] Merge and split operations reversible and audited, with the prior grouping
      recorded so an undo restores it exactly
- [x] Precision sampled and reported — **1.000, with the sample's limits stated**

## 6. Contracts and schema changes
No contract changed. `CanonicalPlace` is the internal ingestion record and is
deliberately wider than the contract's `Place`. The public contract's inability to
express a location is real and is logged as `ENH-003`, not silently fixed here.

## 7. What an identifier is allowed to mean

The allowlist has a stated test rather than a list of namespaces somebody trusted:
**a namespace carries identity only if its identifiers denote at most one venue.**

An identifier that denotes something *coarser* than a venue merges distinct venues
by construction, and does it with the confidence of an exact match:

| Namespace | Denotes | Verdict |
| --- | --- | --- |
| `wikidata`, `osm`, `uic` | one entity | **identity** |
| `address`, `building` | a container — two museums share one | not identity |
| `phone`, `website`, `brand` | a chain — every branch shares one | not identity |
| `gtfs_stop` | a stop *within one feed publication* | not identity — STEP-005.04 established these are not stable across publications |

A shared namespace that is not on the allowlist is **named in the decision** rather
than silently ignored, because to a reviewer "we ignored this evidence" and "there
was no evidence" look identical.

## 8. Telemetry, security and accessibility
No telemetry. No new egress, credential or personal data. No user surface — the
review queue is a service-layer type, and the screen a reviewer needs is UI-step
work under `REQ-A11Y-001` and `REQ-A11Y-003`.

**Tenancy is a decision, not an omission.** Places are reference data and carry no
tenant ID; `BR-046` §7 states the reasoning and hands STEP-006 the job of enforcing
the boundary at the table.

## 9. Tests added
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-004 | integration | Same venue from two providers resolves to one canonical place |
| — | integration | Distinct nearby venues are **not** merged |
| — | unit | Below-threshold match enters the review queue |
| — | measurement | **Zero false merges** across the labelled sample |
| — | measurement | **Zero true duplicates discarded** — the metric that stops precision being satisfied by merging nothing |
| — | measurement | The recorded figures are pinned, so they cannot drift from the code |
| — | unit | A shared website, address or GTFS stop ID never merges |
| — | unit | An identifier conflict blocks a merge that every other signal demands |
| — | unit | A perfect name cannot pay for distance |
| — | unit | Category demotes and never promotes, in both directions |
| — | unit | Swiss spelling variants match; the case where the second normalisation changes the verdict is pinned at 0.857 vs 1.000 |
| — | unit | Undo restores the exact prior grouping; out-of-order undo is refused |
| — | unit | A split must be an exact partition |
| — | structural | The review queue has no method that approves without a human |
| — | regression | `BUG-027` — six refusals |

60 tests. **Mutation testing: 13 seeded, 13 killed** — three only after the gaps
they exposed were closed.

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 985 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One new package, one modified adapter, two modified test modules |
| R4 untested requirements | **PASS — improved** | REQ-DATA-004 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…027; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert the commit. The adapter returns to accepting incomplete payloads, which is
`BUG-027` — so the revert reopens a known defect and is not free.

## 12. Acceptance criteria
- [x] Identifier-first matching implemented, with an allowlist that states its test
- [x] Low-confidence matches queued, not merged — and structurally unapprovable
      without a human
- [x] Merges reversible and audited, with exact prior state recorded
- [x] Precision measured on a labelled sample — **1.000**, alongside the metric that
      makes precision meaningful

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-18 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Measured | precision **1.000**, zero duplicates discarded, recall 0.500, review rate 0.538 over 13 labelled pairs |
| Mutation testing | **13 of 13 killed** — 10 of 13 before the three gaps below were closed |
| Bugs found | **`BUG-027`** — the place record had no coordinate, no category, and manufactured its identifier |
| Risks raised | **`RISK-016`** — the code graph reports zero dependants for symbols that have them |
| Enhancements raised | `ENH-003` (no location in the public contract), `ENH-004` (test the data contract's required fields) |
| Tracker correction | `MASTER_TRACKER`'s blocker table still listed `BLK-002`, `DEC-002`, `DEC-004`, `DEC-008` and `DEC-009` as open while `DECISION_LOG` recorded all five closed, and while the same file's own STEP-005 row said otherwise. Rule 10 makes the tracker the single source of delivery status, so a table inside it contradicting the log is the exact failure that rule exists to prevent. Reconciled |
| Notes / surprises | **The pre-change check said the change was safe and it was wrong.** `impact --include-tests` returned `0 dependants, LOW` for a symbol with eleven call sites. Tests are indexed; their cross-file edges are not — and since no application code wires `services/` yet, tests are the *only* callers of every service symbol there. That verdict has been understating the blast radius of essentially every change in that directory, while reading exactly like reassurance. `RISK-016`.<br><br>**Writing the next sub-step is how I found the last one's defect.** `BUG-027` was invisible from inside `.02`: nothing threw, nothing returned a wrong value, 36 tests passed. It became obvious the moment something tried to *use* the record. An absence is only visible against the contract that requires it, and no test read `DC-EXT-001`.<br><br>**Three mutants survived the first run and all three were real.** The conflict rule was never exercised, because a different rule happened to catch the sample's only conflict pair. The category-promotion mistake had no pair that could detect it. And the two-normalisation name comparison was **indistinguishable from one normalisation** by every assertion I had written — it only changes a verdict on short names, `Bär` against `Baer` scoring 0.857 stripped against 1.000 expanded. The fix was to find the narrow class where the design earns its place and pin the number, not to assert harder on cases that pass either way.<br><br>**A guard from `.05` had already gone stale, and this sub-step is what staled it.** The straight-line-distance blocklist names `haversine`, `distance`, `euclidean`, `great_circle`. This module's function is `metres_between`. The convenience the guard exists to keep out of routing's reach had just become importable without the guard noticing.<br><br>**The review rate is honest, not comfortable.** 0.538 of an adversarial hand-built sample goes to a human. That is a correctness measurement, not a load forecast — at corpus scale it would be impossible, and the real number cannot be known until a provider corpus exists. Saying "precision 1.000" without saying that would be the misleading half of a true statement. |
