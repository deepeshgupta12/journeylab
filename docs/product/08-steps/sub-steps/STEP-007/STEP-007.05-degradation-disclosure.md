---
sub_step_id: STEP-007.05
parent_step: STEP-007
title: Provider-degradation disclosure wiring
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-006]
blast_radius_id: TBD
depends_on: [STEP-007.04]
last_updated: 2026-09-04
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
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Disclosure fatigue. A banner shown on every degraded day is a banner nobody reads, and most days will have something degraded. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Coverage projection consumes `EVT-008` through the `STEP-006.07` consumer framework
- [ ] Disclosure text derived from the read model's `limitations`, not composed in the UI
- [ ] **Cached responses carry their degradation state** — `REQ-EVID-006` names cache-masking as the specific failure
- [ ] Disclosure is announced once per state change, not per render
- [ ] No provider identity in any rendered string, asserted structurally

## 6. Contracts and schema changes
Consumes `EVT-008`. No change.

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
- [ ] Degradation disclosed, including on cached responses
- [ ] No supplier identity reachable from the client
- [ ] Disclosure updates within the projection lag budget

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Mutation testing | — |
| Bugs found | — |
| Notes / surprises | **`REQ-EVID-006` names the exact failure: degradation masked by cached data presented as current.** So the dangerous path is not the uncached one — it is the cache hit that serves yesterday's healthy answer with today's confidence. The cache added in `.01` is where this is decided, one sub-step earlier and in a different file. |
