---
sub_step_id: STEP-008.07
parent_step: STEP-008
title: Accessibility of the sensitive-data collection flow
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PRIV-003, REQ-A11Y-001]
blast_radius_id: TBD
depends_on: [STEP-008.06]
last_updated: 2026-09-04
---

# STEP-008.07 — Accessibility of the sensitive-data collection flow

## 1. Outcome
The flow that collects accessibility needs is itself fully accessible.

## 2. Scope and boundary
**In scope:** Keyboard, screen-reader and focus behaviour across profile, consent and rights surfaces; error and confirmation announcement.

**Not in this sub-step:** Comparison surfaces (`STEP-013`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PRIV-003, REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material — this is a gate, not a design decision. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Full keyboard traversal with visible focus across every sensitive surface
- [ ] Errors and confirmations announced, not only rendered
- [ ] No colour-only signalling on consent state
- [ ] Screen-reader labels that state the purpose of each consent, not just its name
- [ ] axe clean in both device profiles, with the seeded-violation control still failing

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | browser | Keyboard traversal and focus visibility across all sensitive surfaces |
| — | axe | Zero violations, two device profiles |
| — | browser | Consent state is conveyed without relying on colour |
| — | browser | **The seeded-violation control still fails** — a clean run proves nothing if the detector is broken |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
None.

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
Revert the commit. **This is an accessibility regression**, so it is an emergency-only rollback and must be recorded as one.

## 12. Acceptance criteria
- [ ] Keyboard and screen-reader complete
- [ ] axe clean in both profiles
- [ ] No colour-only signalling
- [ ] The negative control still fails

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
| Notes / surprises | **The form that asks about a wheelchair must work for somebody using a screen reader.** If it does not, the product has failed the exact person it is collecting the data for — and the failure is invisible to everybody testing it with a mouse. That is why the seeded-violation control matters more here than anywhere: a green axe run from a broken detector would be the worst possible evidence. |
