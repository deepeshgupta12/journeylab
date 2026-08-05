# BR-002 — Formatting, linting, strict TypeScript and module boundaries

| Field | Value |
| --- | --- |
| Sub-step | STEP-001.02 |
| Requirements | REQ-PLAT-001 (supports ADR-003 via boundary enforcement) |
| Author | Implementation session |
| Date | 2026-08-05 |

## 1. Intent
Establish formatting, linting, strict TypeScript defaults and **module import-boundary enforcement** so that every later file is authored under the same rules, and so `ADR-003` (modular monolith) stays splittable rather than degrading into a ball of mud.

Also fixes `BUG-002`, found by this sub-step's own pre-change analysis.

## 2. Graph state (protocol step 2)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `11e47a6` |
| Graph indexed commit | `11e47a6` |
| **Match?** | **Yes** — graph was stale at `2fe8318`, refreshed per protocol step 3 before proceeding |
| Index timestamp | 2026-08-05 18:22 |
| Coverage | 2,549 nodes / 3,470 edges — **documentation only** |
| Status | **`BLOCKED` for application code — static fallback applied** |

> Knowledge-graph pre-change check: `BLOCKED`. Static fallback applied. Dependency coverage on application symbols is **unverified**. This does not satisfy the `REQ-KG-008` release gate.

**Note:** the graph was found stale on entry. Protocol step 3 was followed — refreshed, re-verified matching `HEAD`, then continued. Proceeding on the stale index would have produced a confidently wrong analysis.

## 3. Target nodes
| Node | Type | Source location | Owner |
| --- | --- | --- | --- |
| Root toolchain config | Config | `/` | Unassigned (`BLK-001`) |
| `pyproject.toml` lint/type config | Config | `/pyproject.toml` | Unassigned |

Static fallback inventory: **0 TypeScript/JavaScript/Python source files**, **0 workspace packages** with a `package.json`. Verified by `git ls-files '*.ts' '*.tsx' '*.js' '*.py'`.

## 4. Dependencies
**Inbound:** none — no source file imports anything yet.
**Outbound:** new dev dependencies (TypeScript, Biome, dependency-cruiser).

## 5. Impact by category
| Category | Affected | Confidence |
| --- | --- | --- |
| Requirements / scope steps | STEP-001.02; REQ-PLAT-001; enables ADR-003 enforcement | High |
| Owners / consumers | None exist | High |
| Frontend / backend code | None yet — rules apply to future files | High |
| APIs / events / schemas | None | High |
| Tables / migrations | None | High |
| Models / prompts / evals | None | High |
| Tests / fixtures | **New** — boundary fixture and guards added | High |
| Services / deployments / infra | None | High |
| Dashboards / alerts / runbooks | None | High |
| Documentation | `ASM-004` revalidation note; `BUG-002` record | High |
| **Repository hygiene** | **`node_modules/` currently tracked — 2 files (`BUG-002`)** | High |

## 6. Data-flow check
Not applicable — no authentication, tenancy, redaction, retrieval, prompt, export or deletion path is touched.

## 7. Classification
`direct` (new config) · `documentation/process` (version revalidation) · **`unknown` reduced to none** by exhaustive filesystem inventory.

## 8. Risk
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | Rules are strict by design; a too-strict rule blocks authoring but breaks nothing at runtime |
| Severity if it occurs | 2 | Config is edited and re-run; no data or runtime consequence |
| Reach | 1 | No users, services or consumers |
| Detectability | 1 | `pnpm verify` fails loudly and immediately |
| Reversibility | 1 | `git revert` restores the prior config |
| **Confidence in this analysis** | 3 | Graph `BLOCKED`, but static fallback is **exhaustive**: provably zero source files exist to be affected |
| Customer criticality | 1 | No customer-facing surface |

**Overall: LOW**

*Same exhaustive-fallback justification as `BR-001`, and for the last time.* From `STEP-002.01` onward, source files exist, the fallback becomes genuinely partial, and confidence can no longer be argued up from a filesystem scan.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | How probed | Residual risk |
| --- | --- | --- | --- |
| **TypeScript version** | Baseline says 6.0; **npm latest is 7.0.2** | `npm view typescript versions` — 6.0.3 is a real stable release | **Flagged for owner** — pinning documented baseline 6.0.3; TS 7 adoption would need a new ADR |
| Boundary rule efficacy with zero packages | Rule cannot be exercised against real packages yet | Mitigated by a dedicated violating fixture | Low — fixture proves the rule fires |
| Biome vs. ESLint ecosystem maturity | Biome 2.5.7 is current | Baseline is silent on linter choice | Low — replaceable; no source depends on it |
| `node_modules` tracked | Found during this analysis | `git ls-files` | **Fixed in this sub-step as `BUG-002`** |

## 10. Required actions
| Action | Type | Owner |
| --- | --- | --- |
| Fix `.gitignore`, untrack `node_modules` | Bug fix | Implementer |
| Guard against tracked build artifacts | Regression test | Implementer |
| Prove boundary rule fires on a violation | Test | Implementer |
| Flag TS 7 availability for `ASM-004` revalidation | Documentation | Implementer → owner |

## 11. Approval
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Repository owner | Deepesh Gupta | Instructed to proceed with STEP-001.02 following the process | 2026-08-05 |

Risk LOW; no additional approval required. **TypeScript 7 adoption is deliberately *not* taken as an implicit decision** — it is surfaced for explicit owner choice.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` result | 0 changed symbols, 4 changed files, risk low |
| Expected new nodes confirmed | Yes — config files and guards only |
| Unexpected consumers found | None |
| New orphan / unowned nodes | *(pending — `CODEOWNERS` still absent, `STEP-001.03` blocked by `BLK-001`)* |
| Regression R1–R7 | **PASS** — see REGRESSION_LOG |

## 13. Disposition
| Field | Value |
| --- | --- |
| Outcome | **merged** |
| Commit / PR | STEP-001.02 commit on `main` |
| Follow-ups | TS 6 vs 7 decision; per-package `tsconfig.json` when packages exist (STEP-002+) |
