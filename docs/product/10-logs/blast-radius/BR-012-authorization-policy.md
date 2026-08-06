# BR-012 — Role and attribute authorization policy

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.03 |
| Requirements | REQ-SEC-004 |
| Decisions raised | `ADR-012`, `DEC-010` |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-009`, which belongs to the STEP-001.05 guard-portability fix. This record is `BR-012`; the front-matter has been corrected.

## 1. Intent (step 1)
One authorization decision point for all 22 operations, derived from `AUTHORIZATION_MATRIX`, with the matrix generating the tests so the document and the behaviour cannot drift apart silently.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `d9be78b` |
| Graph indexed commit | `d9be78b` — re-indexed immediately before analysis (`status` reported stale first; re-indexed rather than proceeding) |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** by the tool — recorded as a gap, not invented |
| Coverage and known gaps | 3,037 nodes / 4,093 edges. **Python application symbols indexed** — 13 functions, 5 classes under `apps/api` |
| Status | **RUNNABLE — not `BLOCKED`** |

> **First pre-change check in this repository that did not need the static fallback.** `RISK-014` was downgraded at STEP-002.02; this is the first record to benefit.

## 3. Target nodes (step 4)
| Node | Type | Location |
| --- | --- | --- |
| `authz.roles` | Module (new) | `apps/api/src/authz/roles.py` |
| `authz.matrix` | Module (new, **generated**) | `apps/api/src/authz/matrix.py` |
| `authz.policy` | Module (new) | `apps/api/src/authz/policy.py` |
| `tools/authz_matrix_source.py` | Parser (new) | shared by generator and drift gate |
| `RequestContext` | **Existing — consumed, not modified** | `apps/api/src/auth/context.py` |
| `opaque_denial` | **Existing — consumed, not modified** | `apps/api/src/auth/errors.py` |

## 4. Dependencies (step 5 — graph-derived, three hops)
`gitnexus impact({target: "RequestContext", direction: "upstream", maxDepth: 3})`:

| Field | Value |
| --- | --- |
| `epistemic` | **`exact`** |
| `risk` | LOW |
| impacted | 5 (4 direct) |
| depth 1 | `auth/events.py`, `auth/dependencies.py`, `auth/db.py`, `auth/__init__.py` — all IMPORTS, confidence 1.0 |
| depth 2 | `tests/api/test_tenant_context.py` |
| processes / modules affected | 0 / 0 |

**Reading it:** this sub-step *consumes* `RequestContext` and does not alter it, so the four existing importers are unaffected by construction. The graph confirms no path outside `auth/` reaches it.

**Inbound to the new code:** none — no endpoint calls `authorize` yet. Same shape as STEP-002.02: the policy is complete and unwired until STEP-004.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-004`; also touches `REQ-ADMIN-002` (four-eyes), `REQ-COLL-003`, `REQ-LIVE-005` (owner-only). Prerequisite for STEP-004 and every later endpoint | High |
| 2 | Owners / consumers | Sole owner; no external consumers | High |
| 3 | Frontend routes / components | **None today.** Constrains STEP-003: client-side role checks are presentation only, and the UI may not distinguish denied from absent | High |
| 4 | Backend services / workflows / jobs | **None exist.** Every future service must call `authorize`; nothing enforces that yet | **Medium — carried gap** |
| 5 | APIs / schemas / clients / webhooks | **None** — `API-001…018` remain `PROPOSED`. This fixes the denial shape they inherit | High |
| 6 | Events / producers / consumers | **None.** Audited decisions (`audit=True`) have no audit sink until STEP-002.07 | **Medium — carried gap** |
| 7 | Tables / columns / migrations / caches / indexes | **None.** No schema change. Delegation records, unlock state and prior-approver identity are *inputs* the caller must supply; their storage is STEP-002.04 / STEP-021 | High |
| 8 | Datasets / models / prompts / retrievers / tools / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+247 tests** (276 total). `AUTHORIZATION_MATRIX` becomes a **test-generating source**: editing it without regenerating fails CI | High |
| 10 | Services / deployments / infrastructure | None. No new runtime dependency | High |
| 11 | Dashboards / alerts / runbooks | `ALRT-SEC-001` still unimplemented (STEP-024). `authorize` returns `reason="cross_tenant_attempt"` specifically so that alert has something unambiguous to fire on — **the signal exists, the alert does not** | **Medium — gap, carried since BR-008** |
| 12 | Documentation / deprecation commitments | `ADR-012`; `DEC-010`; `AUTHORIZATION_MATRIX` §7 marked as generating source; sub-step record; tracker | High |

## 6. Data-flow inspection (step 7 — MANDATORY, security boundary)
Ran against the indexed graph, not by fallback.

| Hop | Element | Tenant/authority-affecting? | Evidence |
| --- | --- | --- | --- |
| 1 | `RequestContext` | Carries actor + tenant, frozen | STEP-002.02 |
| 2 | `authorize` — tenant check | Rejects foreign-tenant resources **before** any role logic | Test asserts `reason == "cross_tenant_attempt"` |
| 3 | `authorize` — matrix lookup | Absent pair ⇒ deny | `service` denied all 22 |
| 4 | `authorize` — condition check | Unproven condition ⇒ deny | 176-cell conditional test |
| 5 | four-eyes | Same actor ⇒ deny | `REQ-ADMIN-002` |
| 6 | `enforce` | Converts denial to the STEP-002.02 opaque 404 | Reason dropped; leak test |

**Ordering is a security property, not a style choice.** Tenant is checked first so a cross-tenant attempt is recorded as such rather than as a relationship failure — `ALRT-SEC-001` depends on that distinction being present in the reason.

## 7. Classification (step 8)
`direct` (new security control) · `security/privacy` · `documentation-coupled` (the matrix now generates code and tests) · **`unknown`:** whether every future endpoint will actually call `authorize` — unenforceable until endpoints exist.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | No caller today; consumes existing types without modifying them (graph-confirmed) |
| Severity if it occurs | **5** | A wrong cell is unauthorized access to trip data or an unreviewed high-impact override |
| Reach | **5** | Every operation in the product routes through this one function |
| Detectability | 2 | 247 tests, all 176 cells exercised, 6/6 mutants killed — **after one false survival caused by my own harness** |
| Reversibility | 2 | Revertible now; **loosening a policy later is a security regression, not a routine revert** (sub-step §11) |
| **Confidence in this analysis** | **4** | Highest so far — graph `epistemic: exact`, no static fallback |
| Customer criticality | 1 | No customers yet |

**Overall: HIGH** — severity × reach. Confidence is materially better than BR-008/BR-011 because the graph answered.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **`DEC-010` — ops_admin approving a high-impact override** | The matrix marks the cell `⚠️📋` but **never states the condition**. §4's four-eyes rule names a *second curator* only | **Open.** Encoded as a condition nothing grants, so it **fails closed**. A test pins that behaviour. Inventing a rule here would have been inventing authorization policy |
| Nothing forces callers to use `authorize` | No endpoints exist | **Open** — STEP-004 must make it structural, not conventional |
| Audited decisions have no sink | `audit=True` is returned and discarded | **Open** — STEP-002.07 |
| Conditions are caller-asserted | `delegation_record`, `explicit_unlock`, `second_curator` are passed in, not verified here | **By design, and a real risk.** The policy cannot verify what it cannot see. Whoever supplies them must prove them — STEP-002.04 / STEP-021 |
| `guest` expiry source | Policy demands a tz-aware expiry; who sets it is `DEC-004` territory | Low — fails closed when absent |

## 10. Required actions (step 10)
Generate the table from the matrix; three-check evaluation in the specified order; deny-by-default everywhere including `service`; owner-only operations; bounded guest capability; four-eyes; matrix-driven tests over all 176 cells; mutation-test the gate itself; record `ADR-012` and `DEC-010`.

## 11. Approval (step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-06 |

**HIGH risk requires owner approval.** Single owner, so author and approver coincide — the `ADR-010` four-eyes gap. Noted with some irony: this is the sub-step that implements four-eyes for the product while the repository itself still cannot satisfy it.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | Three new authz modules, one shared parser, two test modules, docs. No modification to existing `auth/` symbols |
| Regression R1–R7 | **PASS** — 276 tests; R7 12/12; meta-suite 25/25 |
| Mutation testing | **6/6 killed**, including both drift directions |

## 13. Disposition
**Merged.** Two decisions surfaced rather than assumed: the implementation language (`ADR-012`) and an underspecified matrix cell (`DEC-010`). The generator refusing to guess is what exposed the second — it raised on a bare conditional instead of defaulting one.
