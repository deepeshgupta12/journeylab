---
sub_step_id: STEP-003.01
parent_step: STEP-003
title: Design tokens including high-contrast and reduced-motion
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-004, REQ-NFR-013]
blast_radius_id: BR-014
depends_on: [STEP-002.07]
last_updated: 2026-08-05
---

# STEP-003.01 — Design tokens including high-contrast and reduced-motion

## 1. Outcome
Colour, typography, spacing, elevation and motion tokens exist, with high-contrast and reduced-motion variants, so no component invents its own values.

## 2. Scope and boundary
**In scope:** `packages/ui/src/tokens.css`; light/dark, high-contrast and reduced-motion token sets; contrast ratios verified against WCAG 2.2 AA.

**Not in this sub-step:** Components themselves (`.02`–`.04`); product-specific chart palettes ([STEP-013](../../STEP-013-visual-comparison.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-004, REQ-NFR-013 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Whether the chart library honours token-driven theming — verify before committing to it in STEP-013 |
| Blast radius | BR-014 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Colour tokens with AA-verified contrast pairs
- [ ] Typography, spacing and elevation scales
- [ ] Motion tokens plus a reduced-motion variant
- [ ] High-contrast variant
- [ ] **Status tokens paired with a non-colour affordance** (icon or text)

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-004 | component | Every status token has a non-colour counterpart |
| — | unit | All foreground/background pairs meet AA contrast |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-014` post-change section
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
- [ ] Contrast ratios pass AA for every documented pair
- [ ] Reduced-motion and high-contrast variants exist and are applied by media query
- [ ] No component hard-codes a value a token should own

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Reduced motion is a vestibular-safety requirement, not a preference toggle — it must suppress animation, not merely shorten it. |
