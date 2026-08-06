# BR-016 — Cross-tenant isolation test suite

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.06 |
| Requirements | REQ-SEC-002 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-012`, which belongs to STEP-002.03. This record is `BR-016`; the front-matter has been corrected.

## 1. Intent (step 1)
Make `TST-SEC-002` real: tenant A cannot reach tenant B by **any** path, covered in pytest so R7 runs in the fast tier — and make the paths that do not exist yet **impossible to forget**.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `2687bbe` |
| Graph indexed commit | `2687bbe` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** |

## 3. Target nodes (step 4)
`tests/security/test_tenant_isolation.py` (new). No application code is modified — this sub-step is test-only.

## 4. Dependencies (step 5 — graph-derived)
`impact({target: "authorize", direction: "upstream", maxDepth: 3})` → `epistemic: exact`, risk LOW, 1 direct (`enforce`), 1 process, 1 module (`Authz`).

**Outbound:** `authz.policy`, `auth.context`, `auth.db`, `auth.errors`, `auth.events`, `provisioning`, and the RLS policies from migration 001.
**Inbound:** none — nothing imports a test. But **every later sub-step depends on this suite existing**, which is the real dependency and is not visible to the graph.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-002`; STEP-002.06. Every subsequent sub-step inherits this as R7 | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **None** | High |
| 4 | Backend services / workflows / jobs | **None modified.** Job and event *primitives* are exercised; no worker or outbox exists to test | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | `stamp_envelope` exercised; **enforcement belongs to STEP-006** and is a pending vector | High |
| 7 | Tables / migrations / caches / indexes | **No schema change.** Fixtures create and reuse two organizations | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** — vector-store isolation is a pending vector | High |
| 9 | Tests / fixtures / contract suites | **+19 tests** (14 active, 5 pending). R7 now runs in pytest as well as the shell suite | High |
| 10 | Services / deployments / infrastructure | None | High |
| 11 | Dashboards / alerts / runbooks | `ALRT-SEC-001` still unimplemented (STEP-024). The suite asserts a cross-tenant denial is **marked** `audit=True`; nothing consumes that yet | **Medium — carried gap** |
| 12 | Documentation / deprecation commitments | `SECURITY_TESTING` §2; `SUB_STEP_PROTOCOL` R7; sub-step record; tracker | High |

## 6. Data-flow inspection (step 7 — MANDATORY)
The suite *is* the data-flow inspection, expressed as executable assertions:

| Vector | Status | Evidence |
| --- | --- | --- |
| Storage (read / write / list) | **Covered** | RLS denies cross-tenant read, write, and unbound listing |
| Authorization | **Covered** | Every operation × every role against a foreign resource — 198 combinations, not sampled |
| Enumeration | **Covered** | Denial body carries no tenant, role or permission wording |
| Jobs | **Covered at the primitive** | Payload round-trip; missing context raises; no ambient store to inherit |
| Events | **Covered at the primitive** | Conflicting tenant refused; acting tenant stamped |
| Cache | **Pending** | No cache layer (STEP-010) |
| Outbox / events end-to-end | **Pending** | No outbox (STEP-006) |
| Export | **Pending** | No export path (STEP-015 / STEP-022) |
| Vector store | **Pending** | pgvector installed, unused (STEP-010) |
| Domain graph | **Pending** | No graph service (STEP-026) |

## 7. Classification (step 8)
`test-only` · `security/privacy` · `governance` (this is the safety net every later change relies on) · `unknown`: none.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 1 | No application code modified |
| Severity if it occurs | **4** | A weak isolation suite is worse than none — it manufactures confidence in the control protecting every tenant |
| Reach | **5** | Runs at every subsequent sub-step |
| Detectability | 1 | The suite contains its own meta-test |
| Reversibility | 1 | Test-only; **but removing it is a governance regression** (sub-step §11) |
| **Confidence** | 4 | Graph `epistemic: exact`; every claim executed |
| Customer criticality | 1 | No customers yet |

**Overall: MEDIUM** — low likelihood and trivially reversible, but high reach and high severity-if-wrong.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **Five vectors have nothing to test** | Cache, outbox, export, vector store and graph do not exist | **Managed, not open.** Each has a test that detects whether its subsystem has landed: skip while absent, **FAIL** once present. Proven by seeding a fake cache module and an `outbox` table — each converted its placeholder into a failure naming the subsystem |
| Denials are marked for audit but nothing persists them | No audit sink until STEP-002.07 | **Open** — the suite asserts `audit=True` is carried; it cannot assert a record was written |
| Job and event coverage is at the primitive only | No worker, no outbox | **Open** — the enforcing tests belong to STEP-006 and are registered as pending vectors |
| The shell suite and this one overlap at storage | Both assert RLS behaviour | **Deliberate.** The shell suite runs without Python and proves the database in isolation; this one proves the path application code takes. Losing either would lose a distinct guarantee |

## 10. Required actions (step 10)
Two tenants with identical data shapes; storage, authorization, enumeration, job and event vectors; pending vectors that fail when their subsystem lands; a meta-test that breaks RLS on purpose and restores it; wire into the fast tier.

## 11. Approval (step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-06 |

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | One new test module. **No application symbol modified** |
| Regression R1–R7 | **PASS** — 311 Python + 41 TypeScript; shell R7 12/12; meta-suite 36/36 |
| Mutation testing | **3/3 killed** — tenant check removed, audit flag dropped, job context defaulting |
| Pending-vector mechanism | **Proven** — seeded cache module and `outbox` table each produced a failure |

## 13. Disposition
**Merged.** The meta-test earns its place: it disables the RLS policy, asserts the storage vector then leaks, and restores it. Without that, every other assertion in the file could pass with row-level security switched off entirely.
