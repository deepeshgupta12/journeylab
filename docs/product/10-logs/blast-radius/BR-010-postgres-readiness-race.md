# BR-010 — Postgres readiness race and R7 gate misdiagnosis

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.02 pre-work (verification of STEP-002.01) |
| Requirements | REQ-SEC-001, REQ-PLAT-001 |
| Bug | `BUG-009` |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

## 1. Intent (step 1)
Make the local Postgres healthcheck report readiness only when the **real** server is accepting connections, and make the R7 precondition gate distinguish an unreachable database from an absent schema.

## 2. Graph state (step 2 — six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `f544d38` |
| Graph indexed commit | `f544d38` (re-indexed at analysis time) |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor version | not exposed by the tool (recorded, not invented) |
| Coverage | documentation + 1 migration; **0 indexed application symbols at analysis time** |
| Status | **`BLOCKED` for application code — static fallback** |

## 3. Target nodes (step 4)
`docker-compose.dev.yml` (postgres healthcheck); `tests/security/test_tenant_isolation.sh` (precondition gate).

## 4. Dependencies (step 5)
**Inbound:** `pnpm dev`, the R7 suite, and — from this sub-step onward — the integration tests in `tests/api/`.
**Outbound:** the `postgis/postgis` + pgvector image built in `infra/local/postgres/`.

Static fallback is conclusive for the compose file: nothing imports it; it is read only by Docker Compose.

## 5. Impact by category (step 6 — all twelve)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-001` (R7 reliability), `REQ-PLAT-001`; STEP-001.04, STEP-002.01, STEP-002.02 | High |
| 2 | Owners / consumers | Sole owner; every future contributor running `pnpm dev` | High |
| 3 | Frontend routes / components | None | High |
| 4 | Backend services / workflows / jobs | None yet — but every future service connecting at startup inherits the corrected behaviour | High |
| 5 | APIs / schemas / clients / webhooks | None | High |
| 6 | Events / producers / consumers | None | High |
| 7 | Tables / migrations / caches / indexes | None — schema unchanged; only *when* it is considered reachable | High |
| 8 | Datasets / models / prompts / retrievers / evals | None | High |
| 9 | Tests / fixtures / contract suites | **R7 precondition gate rewritten**; R7 becomes deterministic from a cold start | High |
| 10 | Services / deployments / infrastructure | **Local compose healthcheck.** No production infrastructure exists; the same trap applies to any future readiness probe, recorded in the prevention note | High |
| 11 | Dashboards / alerts / runbooks | None implemented (`ALRT-SEC-001` still deferred to STEP-024) | Medium — carried gap |
| 12 | Documentation / deprecation commitments | `BUG-009`; this record | High |

## 6. Data-flow inspection (step 7)
`NOT_APPLICABLE` to authentication, redaction, retrieval, prompt, export or deletion paths. It does touch the **availability** of the tenancy control's test harness, which is why it is treated as security-relevant rather than as a devex annoyance.

## 7. Classification (step 8)
`direct` · `operational/infrastructure` · `test-integrity` · `unknown`: none.

## 8. Risk (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood | 4 | Fires on every cold start — it was simply never exercised |
| Severity | 4 | An intermittently false R7 is worse than no R7: the failure mode is "re-run it and it goes green", which trains people to dismiss the one gate that must never be dismissed |
| Reach | 3 | Every developer and every future CI job that boots the stack |
| Detectability | 4 | Invisible in steady state; only a cold boot reveals it |
| Reversibility | 1 | One-line revert |
| **Confidence** | 1 | Root cause measured directly, not inferred |
| Customer criticality | 1 | No customers |

**Overall: MEDIUM–HIGH** — driven by the credibility of the security gate, not by product impact.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| Other services' healthchecks | `redis-cli ping`, `mc ready local` were not audited for an equivalent init-phase window | **Open** — no evidence of the same pattern, and no evidence against it. Recorded rather than claimed clear |
| Production readiness probes | None exist yet (STEP-027) | The same trap applies; prevention note carried forward |

## 10. Required actions
TCP healthcheck; connectivity probe distinct from schema probe; verify from three cold boots; log `BUG-009` including why the original 12/12 was not evidence of cold-start correctness.

## 11. Approval
MEDIUM–HIGH with a single owner — self-approved. The `ADR-010` four-eyes gap, stated again rather than glossed.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| Regression R1–R7 | **PASS** — R7 12/12 on three consecutive cold boots |
| Meta-suite | 25/25 |

## 13. Disposition
**Merged.** Found only because STEP-002.01 was re-verified from a clean database rather than trusted on its recorded result.
