---
sub_step_id: STEP-007.05
parent_step: STEP-007
title: Provider-degradation disclosure wiring
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-006, REQ-EVID-001, REQ-EVID-003]
blast_radius_id: BR-064
depends_on: [STEP-007.04]
last_updated: 2026-09-14
---

# STEP-007.05 — Provider-degradation disclosure wiring

## 1. Outcome
When a provider degrades, the traveller sees that the answer is degraded — and never learns who degraded it.

## 2. Scope and boundary
**In scope:** `EVT-008` consumption into the coverage projection; disclosure rendering; the degraded-state banner.

**Not in this sub-step:** The health state machine (`STEP-005.10`); the admin surface (`STEP-021`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-006 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date at `8d9d28b` before any edit |
| HEAD / indexed commit | `8d9d28b` / `8d9d28b` |
| Queries run | `impact(get_coverage, upstream)` → **0, LOW, `"epistemic": "exact"` against 8 call sites grep found**, including the production call at `app.py:189`. `RISK-016` #15 — a cross-file call into the API application, exactly the blind spot `BR-063` §2 described. Confidence taken from grep and from the suites: a new required keyword argument is a `TypeError` at every site that omits it |
| Migration present? | **No.** `limitations` was already `jsonb`; the new writer serialises and casts explicitly rather than adding a column |
| Unknown / low-confidence areas | Disclosure fatigue, as recorded — answered by a **polite** live region announced once per state change, not per render, with the count published so the property is testable. **And one unknown nobody had recorded:** no production code wrote `coverage_read_model` at all (`BR-064` §3) |
| Blast radius | **`BR-064` — MEDIUM, confidence HIGH** |
| Approval required? | **No** — MEDIUM with HIGH confidence, and no product question left open |

## 5. Implementation plan
- [x] Coverage projection consumes `EVT-008` through the `STEP-006.07` consumer framework — **already true since STEP-006.09; what was missing was the write to the table** (`read_models.apply_coverage_state`)
- [x] Disclosure text derived from the read model's `limitations`, not composed in the UI
- [x] **Cached responses carry their degradation state** — `REQ-EVID-006` names cache-masking as the specific failure. Answered twice: `observed_at` stamped *before* caching, and a changed-regions set the caller invalidates on
- [x] Disclosure is announced once per state change, not per render
- [x] No provider identity in any rendered string, asserted structurally

## 6. Contracts and schema changes

**The plan said "no change". There is one, and it is additive.**

| Change | Classification |
| --- | --- |
| `Coverage.observed_at` (required, `date-time`) | **`[ADDITIVE]`** — a stronger response guarantee, the same class as `JobEvent.sequence` |
| `EVT-008` | Consumed as declared. No change |
| Schema | None |

`REQ-EVID-006` forbids cached data *presented as current*, and a document with no
observation time cannot help presenting itself as current. `REQ-EVID-001` requires
the observed time on every volatile fact regardless. The field is stamped inside
`read_coverage` before the document is cached, so a cache hit carries the time of the
read that filled the cache rather than the time of the request — `BR-064` §6.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-006 | resilience | **Degradation is disclosed even when the response is served from cache** |
| — | security | No supplier name reaches the DOM — asserted over rendered output |
| — | integration | A health transition updates the disclosure within the projection's lag budget |
| — | browser | The disclosure is announced once per change, not per render |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Provider identity stays internal (`EVT-008` is an internal stream). The public surface carries one aggregate value.

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
Revert the commit; coverage still renders, without the degradation banner. **That is a disclosure regression**, so the rollback is only acceptable as an emergency measure and must be recorded as one.

## 12. Acceptance criteria
- [x] Degradation disclosed, including on cached responses — `observed_at` stamped before caching, and a changed-regions set to invalidate on
- [x] No supplier identity reachable from the client — asserted over the fold state, the SQL, the document and the rendered page
- [x] Disclosure updates within the projection lag budget — **proven within the API's own seam** (write → changed set → invalidate → next read) and bounded by a TTL asserted ≤ 60s. **Not yet proven in production: no `EVT-008` consumer process runs `apply_coverage_state`** (`BR-064` §9)

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-14 |
| Commit SHA | see git log for `STEP-007.05` |
| Pushed | with the commit, per the workflow loop |
| Graph re-indexed at | after the push |
| `main` green and deployable | ✅ `pnpm verify` exit 0 — 1442 py + 101 web + 311 UI + 82 browser + R7 18/18 |
| Mutation testing | **12 seeded, 12 killed** — and mutant 9 survived first, which deleted a redundant guard rather than adding a test (`BR-064` §8) |
| Bugs found | **None in the product.** A real gap found instead: no production code wrote `coverage_read_model`, and the rule for writing it lived only inside a test. Two red runs were not product defects — a dead Docker daemon, and a contract example I missed |
| Notes / surprises | **`REQ-EVID-006` names the exact failure: degradation masked by cached data presented as current.** So the dangerous path is not the uncached one — it is the cache hit that serves yesterday's healthy answer with today's confidence. The cache added in `.01` is where this is decided, one sub-step earlier and in a different file. |
