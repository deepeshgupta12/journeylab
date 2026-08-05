---
sub_step_id: STEP-001.02
parent_step: STEP-001
title: Formatting, linting and strict TypeScript defaults
status: NOT_STARTED
owners: []
requirement_ids: [REQ-PLAT-001]
blast_radius_id: BR-002
depends_on: [STEP-001.01]
last_updated: 2026-08-05
---

# STEP-001.02 — Formatting, linting and strict TypeScript defaults

## 1. Outcome
Formatting and linting run identically on every machine and in CI, and TypeScript 6 strict defaults plus module boundaries are enforced from the first line of code.

## 2. Scope and boundary
**In scope:** `.editorconfig`, `biome.json`, `tsconfig.base.json`, Python lint/type configuration, **module boundary import rules**.
**Not in this sub-step:** ownership (`.03`), local services (`.04`), CI gate wiring beyond lint/type (that is `STEP-027`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-PLAT-001 | `lint` and `typecheck` run from documented commands and pass on an empty workspace | TST-PLAT-001 |

Supports `ADR-003`: module boundary rules are what keep the modular monolith splittable later.

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015 |
| Direct dependents | `.01` workspace configuration |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-002 — LOW reach, affects every future file's authoring rules |
| Approval required? | No |

## 5. Implementation plan
- [ ] `.editorconfig` for whitespace and encoding
- [ ] `biome.json` for formatting and linting with agreed rules
- [ ] `tsconfig.base.json` with TypeScript 6 strict defaults and ES modules
- [ ] Per-package `tsconfig.json` extending the base
- [ ] Python lint/type/test configuration in `pyproject.toml`
- [ ] **Import-boundary rules** preventing cross-module imports that bypass a public module interface
- [ ] Wire `lint`, `format:check` and `typecheck` scripts

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-001 (partial) | CI | Lint and typecheck pass on the empty workspace |
| — | CI | A deliberate boundary-violating import **fails** the build |

## 8. Telemetry, security and accessibility
Lint rules include the accessibility ruleset so a11y issues fail at authoring time rather than at audit.

## 9. Documentation to update
- [ ] Sub-step completion record · `IMPLEMENTATION_LOG` · `REGRESSION_LOG` · `BR-002` · parent §21 · tracker
- [ ] `CONTRIBUTING.md` records the standards

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | Must include `.01` install verification |
| R2 contract compatibility | | N/A |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug tests | | N/A |
| R7 tenant isolation | | N/A |

## 11. Rollback
Revert configuration files; `.01` remains intact and installable.

## 12. Acceptance criteria
- [ ] `lint`, `format:check` and `typecheck` pass on the empty workspace
- [ ] TypeScript strict defaults active
- [ ] A boundary-violating import fails the build
- [ ] Accessibility lint rules active

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Notes / surprises | — |
</content>
