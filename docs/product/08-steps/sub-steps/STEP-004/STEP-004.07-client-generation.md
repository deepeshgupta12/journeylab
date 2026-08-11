---
sub_step_id: STEP-004.07
parent_step: STEP-004
title: Client generation pipeline and no-hand-edit enforcement
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-007]
blast_radius_id: BR-034
depends_on: [STEP-004.06]
last_updated: 2026-08-11
---

# STEP-004.07 — Client generation pipeline and no-hand-edit enforcement

## 1. Outcome
TypeScript and Python clients are generated in CI as build artifacts, and hand-editing one fails the build.

## 2. Scope and boundary
**In scope:** Generation scripts; `packages/contracts/src/generated/`; CI drift detection; generated-path exclusion from the knowledge graph.

**Not in this sub-step:** Client usage in features.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-007 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `73a2780` — indexed commit matched HEAD at pre-change |
| Queries run | `impact(problem, upstream)`; `cypher` for nodes under generated paths; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | `.gitnexusignore` is **redundant** — GitNexus already skips `generated/` by default, so the file removes nothing (BR-034 §4). The outcome is verified; nothing asserts it, so a change of default would go unnoticed. Carried to `STEP-026` |
| Blast radius | **[BR-034](../../../10-logs/blast-radius/BR-034-generated-clients.md) — MEDIUM, confidence HIGH.** The record predicted `BR-028`, which STEP-004.01 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Generate TypeScript and Python clients from OpenAPI — `tools/gen_clients.py`
- [x] Commit generated output with a clear 'do not edit' header
- [x] **CI regenerates and fails on any diff** — `tests/guards/generated-clients.sh`, wired into `pnpm verify`
- [x] Exclude generated paths from graph indexing so coverage is not inflated — `.gitnexusignore`
- [x] Document the regeneration command in the README — "Changing the API contract"

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-007 | Guard meta | A hand-edited generated file fails the build — **seeded and killed** |
| TST-PLAT-007b | Guard meta | A contract change without regeneration fails the build — **seeded and killed** |
| `contract.assert.ts` | Compile-time | 8 assertions that the generated types did not degrade to `unknown`; **all 8 mutation-tested** |
| `test_conflicting_sources_are_retained_not_averaged` | Python | BUG-020 regression — a conflict must carry provenance and validity |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) IMPL-031 · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) BUG-020
- [x] `BR-034` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)
- [x] README — regeneration workflow, and 4 stale counts corrected

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 592 Python + 61 web + 307 UI + 40 browser; `pnpm verify` green end to end |
| R2 contract compatibility | **PASS — and this was the last free moment** | `Evidenced.conflicts[]` narrowed (BUG-020). `.06` predicted that such a change becomes breaking once clients exist; the fix and the first generation are in the **same commit**, so no client was ever generated from the defective shape |
| R3 graph diff as expected | **PASS** | 58 symbols, 1 affected process (the generator's own flow). **No generated-client symbols appear** — the exclusion confirmed |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-007 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…020; meta-suite **47/47** |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Clients generated for both languages — 2,022 lines TypeScript, 71 Pydantic classes
- [x] Hand edit fails the build — seeded, exit 1, in the guard meta-suite
- [x] Stale client fails the build — seeded, exit 1, in the guard meta-suite
- [x] Generated paths excluded from graph coverage — verified by Cypher at `7b1489e`. **Achieved by GitNexus's own default, not by `.gitnexusignore`, which is redundant here — BR-034 §4**

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | **BUG-020** — a retained evidence conflict could not name its own source. Found by the generator, not by any test |
| Notes / surprises | **Generating a client is a second reader of the contract, and that turned out to be the point.** 470 Python assertions all agreed `openapi.yaml` was correct because they were reading the document that was wrong. The generator produced a different representation of the same contract, and `Record<string, never>` — an object permitted to hold nothing — is a shape a human notices instantly. That is BUG-020, and no amount of additional YAML assertions would have surfaced it.<br><br>**The test that missed it asserted a key, not a capability**: `assert "conflicts" in properties`. This is now the fourth assertion in STEP-004 written against the existence of a thing rather than the property the requirement names — `.02` and `.03` had stale extent assertions, `.06` had one that would have gone vacuous rather than red. Four occurrences in seven sub-steps is a habit, not a coincidence, and **`.08` should hunt for it deliberately** rather than hope to trip over the fifth.<br><br>**`tsc --noEmit` is not a test of a generated client.** It proves the file parses, which it would do just as happily if every schema had collapsed to `unknown` — a live risk, because `.06` moved four schemas behind external `$ref`s and an unresolved external ref degrades rather than errors. Hence `contract.assert.ts`, written with an `Exact<>` helper rather than `extends`, because `extends` is satisfied by `unknown` on the right-hand side.<br><br>**Third tool broken by ADR-009.** `openapi-typescript` v7 builds output through the TypeScript compiler API, which TypeScript 7 does not ship. Pinned to v6. After BUG-017 and BUG-018 this is a property of the ecosystem, and the next generator this repository adopts should be checked for it before adoption rather than after.<br><br>**Two mistakes of my own worth naming.** I copied `packages/ui`'s tsconfig into a package with no components, no Node dependency and no tooling — it failed on the first typecheck with `TS2688`. And `package.json` exported `./src/index.ts`, which did not exist; nothing imported the package, so nothing failed. A broken entry point stays invisible until the first consumer.<br><br>**The graph exclusion is met, and the control I wrote is not what meets it.** A Cypher query returns no nodes under either generated path — but removing `.gitnexusignore` entirely produces a byte-identical index, because GitNexus already skips `generated/` by default. A control probe (ignoring `tools/gen_clients.py` instead) removed 16 nodes, which is how I know the file works and the null result is genuine rather than a bad pattern.<br><br>I had written this up as "exclusion verified" before running that probe. It would have been true of the outcome and false about the cause — the kind of claim that costs somebody a day the first time they rely on the file to exclude something new. Corrected in BR-034 §4 in a follow-up commit, and the residual gap (nothing **asserts** the absence, so a changed default would pass silently) is carried to `STEP-026`. |
