# BR-009 — README guard portability (CI failure fix)

| Field | Value |
| --- | --- |
| Sub-step | Follow-up to STEP-001.05 |
| Requirements | REQ-PLAT-001 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-05 |

## 1. Intent (step 1)
Fix `readme-accuracy.sh` check 4, which fails on `ubuntu-latest` because it asserts a macOS Homebrew path exists. Make the check portable **without weakening it** into something that cannot catch README drift.

## 2. Graph state (step 2 — six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `2f23670` |
| Graph indexed commit | `2f23670` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor version | not exposed by the tool (recorded, not invented) |
| Coverage | documentation + 1 migration; **0 indexed application symbols** |
| Status | **`BLOCKED` for application code — static fallback** |

## 3. Target nodes (step 4)
`tests/guards/readme-accuracy.sh` check 4; `README.md` prerequisites section.

## 4. Dependencies (step 5)
**Inbound:** `pnpm verify` (local + CI `verify.yml`). **Outbound:** `README.md`, `.nvmrc`.
No application code imports either. Static fallback is conclusive for this file.

## 5. Impact by category (step 6 — all twelve)
| # | Category | Affected |
| --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-PLAT-001`; STEP-001.05 |
| 2 | Owners / consumers | Sole owner; CI is the only other consumer |
| 3 | Frontend routes / components | None |
| 4 | Backend services / workflows / jobs | None |
| 5 | APIs / schemas / clients / webhooks | None |
| 6 | Events / producers / consumers | None |
| 7 | Tables / migrations / caches / indexes | None |
| 8 | Datasets / models / prompts / retrievers / evals | None |
| 9 | Tests / fixtures / contract suites | **`readme-accuracy.sh` + its meta-test entry in `meta/run-all.sh`** |
| 10 | Services / deployments / infrastructure | **CI `verify.yml` — currently red on `main`** |
| 11 | Dashboards / alerts / runbooks | None |
| 12 | Documentation / deprecation commitments | `README.md` prerequisites wording |

## 6. Data-flow inspection (step 7)
`NOT_APPLICABLE` — no authentication, tenancy, redaction, retrieval, prompt, export or deletion path is touched.

## 7. Classification (step 8)
`direct` · `operational/deployment` (CI is red) · `unknown`: none.

## 8. Risk (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood | 1 | Single, well-understood check |
| Severity | 2 | CI red blocks the merge gate — process impact, not product |
| Reach | 2 | Every future PR passes through `verify` |
| Detectability | 1 | CI reports it immediately |
| Reversibility | 1 | `git revert` |
| **Confidence** | 2 | Cause reproduced and understood from the CI log |
| Customer criticality | 1 | None |

**Overall: LOW**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| Other host-specific assumptions in guards | Only this one had been exercised by CI | **Probe found 2 more**: BSD sed in the meta-suite, and a misleading uv-missing error. All three fixed |

## 10. Required actions
Make check 4 portable; keep it able to catch real drift; probe every guard for other absolute-path assumptions; extend the meta-suite.

## 11. Approval
LOW risk — no additional approval beyond the owner.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| Regression R1–R7 | **PASS** — incl. all 11 guards verified under Linux |
| CI green | **Proven in a node:24-bookworm container**; real GitHub run still the final word |

## 13. Disposition
**Merged.** Probing beyond the reported failure found two further portability defects that had not yet been exercised. All 11 guards now pass under Linux.
