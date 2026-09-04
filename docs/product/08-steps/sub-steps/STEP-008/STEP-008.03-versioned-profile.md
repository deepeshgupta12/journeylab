---
sub_step_id: STEP-008.03
parent_step: STEP-008
title: Versioned traveller profile with hard and soft separation
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PRIV-003, REQ-TRIP-004]
blast_radius_id: TBD
depends_on: [STEP-008.02]
last_updated: 2026-09-04
---

# STEP-008.03 — Versioned traveller profile with hard and soft separation

## 1. Outcome
Accessibility needs are recorded as declarations, versioned, and never mixed with preferences.

## 2. Scope and boundary
**In scope:** `traveler_profiles` writes; the hard/soft boundary; version-on-change; the declaration-only path.

**Not in this sub-step:** The brief's constraint classes (`STEP-009.05`); consent (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PRIV-003, REQ-TRIP-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | How to word accessibility capture so it collects what the solver needs without becoming an interrogation. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Every change writes a new version; **no in-place edit**, so a scenario can cite the profile it was solved against
- [ ] Accessibility entries are **hard constraints** and stored separately from preferences (`constraint-class.json`)
- [ ] **Declaration only** (`REQ-PRIV-003`) — there is no inference path, and no field a derived value could be written to
- [ ] Each entry records who declared it (`traveler` or `advisor_on_behalf`) and its consent reference
- [ ] Sensitive attributes are never used outside the purpose consented to

## 6. Contracts and schema changes
Writes `DATA-003` as modelled in `010_domain.sql`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-003 | integration | **No code path writes an accessibility entry that was not declared** — structural, as in STEP-005.02 |
| — | integration | Editing a profile creates a version rather than mutating one |
| — | unit | A hard accessibility constraint cannot be stored as a preference |
| — | security | A profile is unreadable across tenants |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
**No sensitive attribute in any telemetry, trace attribute or event payload.** Not hashed, not bucketed — absent.

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
Revert the commit. Existing versions stay; they are the evidence of what was declared and when.

## 12. Acceptance criteria
- [ ] Accessibility is declared, never inferred
- [ ] Every change is a new version
- [ ] Hard and soft stay separate
- [ ] Nothing sensitive reaches telemetry

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
| Notes / surprises | **Merging a wheelchair requirement into preferences produces a solver that trades it away for nine minutes** — `constraint-class.json` says so in exactly those words. The separation has to survive the *UI*, where a single settings form is the obvious design and quietly puts both on one screen with one save button. |
