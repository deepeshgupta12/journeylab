# BR-017 — Audit event emission and runtime flag primitives

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.07 |
| Requirements | REQ-SEC-007, REQ-PLAT-012 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-013`, which belongs to STEP-002.04. This record is `BR-017`; the front-matter has been corrected.

## 1. Intent (step 1)
Give the audit obligations accumulated since `.03` somewhere to go — immutably, separately from application logs, redacted at emission — and add flag primitives whose failure mode is conservative rather than permissive.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `d7d71cf` |
| Graph indexed commit | `d7d71cf` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** |

## 3. Target nodes (step 4)
| Node | Type | Location |
| --- | --- | --- |
| `audit_events`, `feature_flags` | Tables (new) | `db/migrations/002_audit_and_flags.sql` |
| `audit` | Module (new) | `services/audit/src/audit.py` |
| `redaction` | Module (new) | `services/audit/src/redaction.py` |
| `flags` | Module (new) | `services/audit/src/flags.py` |

## 4. Dependencies (step 5 — graph-derived)
`impact({target: "AuditRecord", direction: "upstream", maxDepth: 3})` → `epistemic: exact`, risk LOW, 2 direct — **both of them tests**.

That zero-production-consumer result is the point: `provisioning` has been returning `AuditRecord` since `.04` and `authz` has been returning `Decision.audit` since `.03`, with nothing to receive either. This sub-step is that sink.

**Outbound:** migration 001's `app_current_org()` and the `journeylab_app` role.
**Inbound:** none yet — wiring the emitters into request paths belongs to `STEP-004`.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-007`, `REQ-PLAT-012`; closes gaps carried from `.03`, `.04`, `.06` | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **None.** The admin console that edits flags is `STEP-021` | High |
| 4 | Backend services / workflows / jobs | New `services/audit/`. No existing service modified | High |
| 5 | APIs / schemas / clients / webhooks | **None** — no endpoint emits yet | High |
| 6 | Events / producers / consumers | **None.** Audit is a table, deliberately not the event bus — an audit trail routed through a queue can be dropped | High |
| 7 | Tables / migrations / caches / indexes | **Migration 002 — two new tables, both RLS-enforced.** `audit_events` is append-only **by privilege**; `feature_flags` is read-only to the application | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** — but model and provider flags are the mechanism `STEP-019` will use to roll back a model without a deploy | High |
| 9 | Tests / fixtures / contract suites | **+29 tests** (335 Python total) | High |
| 10 | Services / deployments / infrastructure | New Python path `services/audit/src`. No new dependency | High |
| 11 | Dashboards / alerts / runbooks | §8 wants audit volume and write-failure rate monitored. **Not implemented** — `STEP-024`. `emit` raises rather than swallowing, so a failure is at least loud at the call site | **Medium — carried gap** |
| 12 | Documentation / deprecation commitments | `SC-AUDIT-01` marked implemented; sub-step record; tracker | High |

## 6. Data-flow inspection (step 7 — MANDATORY, redaction paths)
| Hop | Element | Sensitive data? | Evidence |
| --- | --- | --- | --- |
| 1 | Caller builds `AuditEvent` | May contain anything | Naive timestamps rejected at construction |
| 2 | `redact()` | **Masks by key name and by value shape** | Sensitive keys; JWT, Bearer, `sk-`, PEM and long-hex value patterns |
| 3 | `redact()` — email | PII | Reduced to its domain; local part removed |
| 4 | `redact()` — final sweep | Anything still credential-shaped | **Raises**, blocking the write |
| 5 | `emit()` INSERT | Redacted payload only | Any driver failure raises `AuditWriteError` |
| 6 | Storage | Tenant-scoped | RLS `ENABLE` + `FORCE`; policy on `app_current_org()` |
| 7 | Modification | **Impossible for the application** | `journeylab_app` has INSERT + SELECT only; UPDATE/DELETE/TRUNCATE all return `permission denied` — verified |

## 7. Classification (step 8)
`direct` · `data/schema` (migration 002) · `security/privacy` · `unknown`: none.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | No existing code modified; new tables only |
| Severity if it occurs | **5** | Two distinct catastrophes: a secret written into a store that cannot delete it, or a flag outage that **enables** an unfinished feature |
| Reach | 4 | Every audited operation and every flagged feature, forever |
| Detectability | 2 | 29 tests, 4/4 mutants killed |
| Reversibility | **5** | **Audit rows never revert** — append-only by design. A bad writer is fixed forward (sub-step §11) |
| **Confidence** | 4 | Graph `epistemic: exact`; append-only proven against the live database |
| Customer criticality | 1 | No customers yet |

**Overall: HIGH** — severity and irreversibility, not likelihood.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **Audit retention is not legally validated** | Named by the sub-step; depends on `DEC-007` (residency) | **Open.** No retention policy is implemented; rows accumulate indefinitely. That is the safe direction for evidence but not a compliance answer |
| Redaction is pattern-based | New credential formats will not match existing patterns | **Inherent.** Mitigated by the final sweep refusing anything still credential-shaped, and by masking on key name as well as value |
| Nothing emits yet | No endpoint calls `emit` | **Open** — `STEP-004` wires it. The sink existing is the precondition |
| No write-failure monitoring | §8 asks for it | **Open** — `STEP-024`. `emit` raises rather than swallowing |
| The table owner can still modify rows | Unavoidable in PostgreSQL | **Accepted, documented.** The application never connects as the owner (`STEP-002.01`) |

## 10. Required actions (step 10)
Append-only by privilege, not convention; redaction at emission with a fail-closed sweep; separate store; flags with a required conservative value and no permissive failure path; prove the app role cannot update, delete or truncate.

## 11. Approval (step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-06 |

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | Migration 002, three new modules, one test module. No existing symbol modified |
| Regression R1–R7 | **PASS** — 335 Python + 41 TypeScript; shell R7 12/12; isolation suite 14+5; meta-suite 36/36 |
| Mutation testing | **4/4 killed** |

## 13. Disposition
**Merged.** Two real defects were found by the tests rather than by review: `PRIMARY KEY (key, organization_id)` made the NULL-means-global row impossible to insert (PK columns are implicitly NOT NULL), and a tuple containing a private key passed through `redact()` completely untouched because neither the masker nor the sweep traversed tuples. The fail-closed branch was decorative until that second fix.
