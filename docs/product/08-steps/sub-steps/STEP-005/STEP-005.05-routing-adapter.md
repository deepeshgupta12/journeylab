---
sub_step_id: STEP-005.05
parent_step: STEP-005
title: Routing engine adapter with explicit profile declaration
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-A11Y-003]
blast_radius_id: BR-044
depends_on: [STEP-005.04]
last_updated: 2026-08-17
---

# STEP-005.05 — Routing engine adapter with explicit profile declaration

## 1. Outcome
Travel-time matrices are computed per mode and time window, and the provider **declares which profiles it genuinely supports** — including wheelchair.

## 2. Scope and boundary
**In scope:** `services/routing/src/matrix.py`; provider-independent profile interface; matrix caching keyed by mode, window and licence terms.

**Not in this sub-step:** Solver consumption ([STEP-012](../../STEP-012-scenario-optimisation-and-simulation.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-A11Y-003 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `8bf34e0` — matched HEAD at pre-change |
| Queries run | `cypher` over `services/routing` — 0 nodes, a new service root; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **`DEC-008` remains open**, and a recommendation is now on the table (§13) rather than deferred, because this sub-step has been reached. It did **not** block: the scope asked for a provider-independent interface and nothing here depends on the answer. **Wheelchair data quality is still unknown** — no live routing call has been made, so profile support is a shape this code demands a provider declare, not a fact about any provider |
| Blast radius | **[BR-044](../../../10-logs/blast-radius/BR-044-routing-adapter.md) — MEDIUM, confidence HIGH.** The record predicted `BR-034`, which STEP-004.07 holds; corrected here |
| Approval required? | **No** for the code. `DEC-008` needs an owner decision |

## 5. Implementation plan
- [x] Provider-independent `Profile`: walking, transit, driving, **wheelchair**
- [x] **`resolve_profile` returns the profile or a refusal — the type admits no downgrade.** `ProfileUnsupported` carries no duration field at all, not even a nullable one
- [x] Time-dependent: `departure_at` is part of every result, distinct from `computed_at`
- [x] `MatrixKey` includes **`licence_id`** as part of its identity, so differently-licensed matrices cannot share a cache entry
- [x] **No straight-line substitution**, enforced twice: a non-positive duration raises, and a structural test asserts no haversine or distance helper exists
- [x] `assumptions` required on every travel time, even when it states the default

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-003 | integration | Wheelchair profile unsupported ⇒ **explicit limitation**, not silent walking substitution |
| — | unit | Straight-line distance never appears in a matrix result |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [x] `BR-044`
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 863 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | A new service root, `services/routing/` |
| R4 untested requirements | **PASS — improved** | REQ-A11Y-003 gains its first enforcement outside the web layer |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…025; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Four profiles behind one interface
- [ ] Profile support declared explicitly
- [ ] Time-dependent matrices correct
- [ ] Cache key includes licence terms
- [ ] No straight-line fallback anywhere

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-17 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. One mistake of my own — a stray `__init__.py` — see below |
| **`DEC-008` recommendation (owner decision needed)** | **OpenTripPlanner 2, self-hosted.** Rationale: it consumes exactly the two feeds `ADR-016` already chose — Swiss national GTFS and OSM — so it adds no new data dependency and no licence question beyond the ones already open. It is the only open-source option that routes **transit and step-free together**, using GTFS accessibility fields alongside OSM kerb, lift and ramp tags, which is what `REQ-A11Y-003` needs. Zero licence spend, satisfying the constraint set for `DEC-002`.<br><br>**The cost, stated plainly:** self-hosting is an operational burden that arrives before Phase 1 — graph builds on every feed change, memory proportional to network size, and a service to keep alive. This is the same shape as `ADR-015`'s Kafka decision, and it should be accepted with that cost in view rather than on the licence argument alone.<br><br>**Runner-up:** Valhalla — lighter to operate and faster, but its pedestrian profile is not step-free routing, so `Profile.WHEELCHAIR` would have to be declared unsupported. That is *permitted* by this sub-step's design and is exactly what the refusal path is for; it is simply a worse product. **Rejected:** OSRM (no transit, no accessibility). |
| Notes / surprises | **The prohibition is the sub-step.** A wheelchair user handed walking times receives an itinerary computed for somebody who can take stairs, and it will look correct — every duration plausible, the Bern transfer needing a footbridge reading as nine minutes. There is no way for the person to know, which is what makes it worse than a refusal. So `resolve_profile` returns the profile *or* a refusal and the type admits no third outcome, and `ProfileUnsupported` has no duration field at all — a nullable one is one `or 0` away from becoming a travel time.<br><br>**The disclosure is asserted on its wording, not its presence.** A correct type with copy that lets "no step-free data" read as "step-free" would satisfy the requirement's letter and fail its purpose, so the test names three phrases the text must contain.<br><br>**One test is structural rather than behavioural, deliberately.** It asserts the module exposes no haversine, distance or great-circle helper. The failure mode is somebody adding that convenience later and a colleague reaching for it; behaviour cannot catch that, only absence can.<br><br>**A stray `__init__.py` made mypy see one file as two modules.** I created `services/routing/src/__init__.py` from habit — neither other service root has one, because `src` is a path root, not a package. Copying a shape from memory instead of from the neighbouring service is the same mistake as `packages/contracts`' tsconfig in STEP-004.07.<br><br>**Still unverified across all five adapters:** no live call has been made to any provider. Profile support, field names, ensemble spread and the alert SLO are all shapes this code demands rather than facts about anyone's API. `.07` is where that meets reality. |
