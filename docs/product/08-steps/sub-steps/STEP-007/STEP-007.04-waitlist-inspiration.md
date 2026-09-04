---
sub_step_id: STEP-007.04
parent_step: STEP-007
title: Waitlist and inspiration mode with consent
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-002, REQ-PRIV-002, REQ-PRIV-004]
blast_radius_id: TBD
depends_on: [STEP-007.03]
last_updated: 2026-09-04
---

# STEP-007.04 — Waitlist and inspiration mode with consent

## 1. Outcome
Somebody outside coverage can ask to be told when it opens, having explicitly consented to being contacted for that purpose alone.

## 2. Scope and boundary
**In scope:** Waitlist capture; a purpose-specific consent record (`DATA-016`); inspiration content for uncovered regions.

**Not in this sub-step:** Email delivery (operations); account creation (`STEP-008`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-002, REQ-PRIV-002, REQ-PRIV-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Whether inspiration content for an uncovered region is useful or misleading. Showing a beautiful page for a place we cannot plan may read as a promise. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Waitlist entry writes a `ConsentRecord` with **purpose `waitlist_notification` only**
- [ ] Consent is independently withdrawable without affecting any other purpose (`REQ-PRIV-004`)
- [ ] No pre-ticked boxes; consent is an action, not a default
- [ ] Inspiration content clearly marked as not plannable yet
- [ ] Email stored against the consent record, deletable on withdrawal (`REQ-PRIV-006`)

## 6. Contracts and schema changes
Consumes the `ConsentRecord` shape from `DATA-016`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-004 | integration | Withdrawing waitlist consent leaves other purposes intact |
| — | integration | **Withdrawal deletes the email**, traversing every store that holds it |
| — | browser | No consent control is pre-selected |
| — | unit | A waitlist entry without a consent record is refused |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
The waitlist email is personal data from the moment it is typed. It is never logged, never in a trace attribute and never in an event payload (`EVENT_CONTRACTS` §2).

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
Revert the commit and delete captured entries — the consent basis disappears with the feature, so retention would be unlawful.

## 12. Acceptance criteria
- [ ] Waitlist entry requires explicit, purpose-specific consent
- [ ] Withdrawal is independent and deletes the email
- [ ] No pre-ticked consent
- [ ] Inspiration content does not imply plannability

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
| Notes / surprises | **Rolling this back is not just reverting code.** The consent basis for holding those emails is the feature itself, so a revert that leaves the rows behind converts a rollback into a retention problem. This is the first sub-step where the rollback plan has a legal component, and it will not be the last. |
