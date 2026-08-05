# JourneyLab — Mandatory Pre-Change Impact Protocol

> **This protocol is binding. No code, schema, API, event, model, prompt, infrastructure or configuration change may begin until steps 1–12 are complete and recorded.** (`REQ-KG-008`)

| Field | Value |
| --- | --- |
| Owner | Platform + TPM (unassigned — `BLK-001`) |
| Status | `READY` — binding from the first code commit |
| Tool | GitNexus (`ADR-005`) — **verified installed and indexing** on 2026-08-05 |
| Current capability | **`BLOCKED` for application code** — the index covers Markdown documentation only (`RISK-014`) |
| Last reviewed | 2026-08-05 |

Navigation: [Blast radius template](BLAST_RADIUS_TEMPLATE.md) · [Query playbook](GRAPH_QUERY_PLAYBOOK.md) · [Indexing & refresh](INDEXING_AND_REFRESH.md) · [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Why this exists

The failure this prevents is specific: a change that looks local but is not. A renamed field breaks a generated client; a tightened validator breaks an ingestion backfill; a solver-config change silently invalidates every stored scenario's reproducibility. Grep finds text; the graph finds **dependencies**, including through APIs, events, tables, models and tests.

The second failure it prevents is **regression from accumulated work** — a fix in sub-step 4 quietly breaking what sub-step 2 delivered. That is why the protocol runs at **every sub-step**, not once per major step.

---

## 2. Before any change — steps 1 to 12

### Step 1 — Establish intent
Record the target requirement (`REQ-*`), scope step (`STEP-NNN`), sub-step (`STEP-NNN.MM`) and the intended user or system outcome. A change without a requirement is either undocumented scope or unnecessary work.

### Step 2 — Confirm the graph indexes current `HEAD`
Record all six fields:

| Field | How to obtain |
| --- | --- |
| Repository and branch | `git rev-parse --abbrev-ref HEAD` |
| `HEAD` commit | `git rev-parse HEAD` |
| Graph indexed commit | `npx gitnexus status` |
| Index timestamp | `npx gitnexus status` |
| Extractor/schema version | `npx gitnexus status` / repo context resource |
| Coverage and known gaps | Graph-quality report ([GRAPH_QUALITY_AND_GOVERNANCE](GRAPH_QUALITY_AND_GOVERNANCE.md)) |

```bash
git rev-parse --abbrev-ref HEAD && git rev-parse HEAD
npx gitnexus status
```

### Step 3 — Refresh if stale
If the graph is stale, incomplete for the target path, or at a different commit:

```bash
npx gitnexus analyze          # incremental
npx gitnexus analyze --force  # if the index is suspect or corrupt
```

**Do not proceed on a stale graph.** A stale impact analysis is worse than none, because it produces false confidence.

### Step 4 — Locate target nodes
Find each target by stable identifier and source location, not by text search:

```
mcp__gitnexus__context({ name: "<symbol>" })
mcp__gitnexus__query({ query: "<concept>" })
```

### Step 5 — Traverse dependencies
Query inbound and outbound dependencies for **at least three hops**, or until a stable domain boundary is reached:

```
mcp__gitnexus__impact({ target: "<symbol>", direction: "upstream" })
mcp__gitnexus__impact({ target: "<symbol>", direction: "downstream" })
```

### Step 6 — Enumerate every affected category
The analysis is incomplete unless each category is either listed or explicitly marked "none found, confidence X":

- requirements and scope steps
- owners and consumers
- frontend routes and components
- backend services, functions, workflows, jobs
- APIs, schemas, generated clients, webhooks
- events, producers, consumers
- tables, columns, migrations, caches, indexes
- datasets, features, models, prompts, retrievers, tools, evaluations
- tests, fixtures, contract suites
- services, deployments, infrastructure
- dashboards, alerts, runbooks
- documentation and deprecation commitments

### Step 7 — Data-flow inspection for sensitive changes
For security- or privacy-relevant changes, inspect control/data-flow and taint paths:

```
mcp__gitnexus__pdg_query({ ... })   # control/data dependence
mcp__gitnexus__trace({ ... })       # source → sink flow
```

Mandatory when touching: authentication, authorization, tenancy, redaction, retrieval inputs, model prompts, export or deletion.

### Step 8 — Classify each impact
`direct` · `indirect` · `runtime-only` · `data/schema` · `contract/consumer` · `security/privacy` · `AI/model/evaluation` · `operational/deployment` · `documentation/process` · **`unknown`**

`unknown` is a required, legitimate category. Using it honestly is the point.

### Step 9 — Score blast radius
Score on likelihood, severity, reach, detectability, reversibility, **confidence** and customer criticality per [BLAST_RADIUS_TEMPLATE](BLAST_RADIUS_TEMPLATE.md).

> **Low confidence never becomes low risk.** If dependency coverage is unknown, the risk score reflects the uncertainty. Collapsing unknown coverage into "low risk" is the single most common way this protocol is defeated.

### Step 10 — Record required actions
Tests, migration, compatibility, rollout, monitoring and rollback actions implied by the analysis.

### Step 11 — Obtain approval
Required for **high, critical or materially uncertain** impact. Approver must be the owning reviewer, never the author.

### Step 12 — Only now, implement.

---

## 3. After implementation — verification

1. Run the required unit, integration, contract, end-to-end, security, data, AI/ML, performance and resilience checks.
2. **Re-index at the implementation commit:** `npx gitnexus analyze`
3. Compare pre- and post-change graph neighborhoods.
4. Confirm expected new/removed nodes and edges — and only those.
5. Investigate **unexpected consumers, orphan nodes, ownership gaps and untested requirements**.
6. Update API/event/data contracts and regenerate clients.
7. Update the step file, sub-step file, [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md), architecture docs, runbooks and [DECISION_LOG](../02-delivery/DECISION_LOG.md).
8. Record deployment, feature-flag, monitoring and rollback readiness.
9. Attach final graph query evidence and the release/PR reference.
10. Mark the step `VERIFIED` **only** when exit criteria and evidence are complete.

```
mcp__gitnexus__detect_changes()   # before committing — confirms only expected scope changed
```

---

## 4. Regression cross-check at every sub-step

**Required by the repository owner:** each sub-step must confirm that previous implementations and fixes still work.

| # | Check | Command / query | Pass condition |
| --- | --- | --- | --- |
| R1 | Full regression suite for all completed sub-steps of this step **and** all previously `VERIFIED` steps | `pnpm test && pytest` (scoped runner defined in `STEP-027`) | All green; no skipped tests without a recorded reason |
| R2 | Contract compatibility against the last release | CI contract diff | No unintended breaking diff |
| R3 | Graph diff shows only intended changes | `mcp__gitnexus__detect_changes()` | No unexpected symbol, edge or flow change |
| R4 | No previously satisfied requirement lost its test | `KG-Q-008` untested-requirement query | Count does not increase |
| R5 | No new orphan or unowned node | `KG-Q-008` | Count does not increase |
| R6 | Fixed bugs stay fixed | Regression tests from [BUG_REGISTER](../10-logs/BUG_REGISTER.md) | Every closed bug's test still passes |
| R7 | Cross-tenant isolation intact | `TST-SEC-002` | Pass — **non-negotiable** |

**If any check fails, the sub-step is not complete.** Fix forward or revert; do not proceed to the next sub-step with a red regression.

---

## 5. Commit and push cadence

Per the repository owner's directive, work proceeds **one sub-step at a time**, each ending in a commit and push:

1. Complete the sub-step's implementation and tests.
2. Run the §4 regression cross-check.
3. Run `mcp__gitnexus__detect_changes()`.
4. Update the sub-step file's completion record and the logs in [`10-logs/`](../10-logs/).
5. Commit — **without AI co-authorship attribution** (`ADR-006`).
6. Push.
7. Re-index: `npx gitnexus analyze`.

Full detail in [SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md).

---

## 6. Static fallback — when the graph cannot answer

**Currently in force for application code**, because the index contains documentation only (`RISK-014`).

| Substitute | Method |
| --- | --- |
| Symbol dependencies | `rg` across the repo for the identifier, its string form and its generated variants |
| API consumers | Search generated clients, contract tests and the OpenAPI file |
| Event consumers | Search topic names in AsyncAPI and consumer registrations |
| Data dependencies | Search migrations, ORM models and raw SQL for table/column names |
| Model/prompt dependencies | Search the prompt registry and evaluation datasets |
| Test coverage | Search test files for the symbol and its requirement ID |
| Ownership | `CODEOWNERS` |

**Mandatory statement whenever the fallback is used:**

> Knowledge-graph pre-change check: `BLOCKED`. Static fallback applied. Dependency coverage is **unverified**; unknown-impact confidence is low. This does **not** satisfy the `REQ-KG-008` release gate.

Never claim the graph was queried when it was not.

---

## 7. Exemptions

| Exempt | Not exempt |
| --- | --- |
| Documentation-only changes with no contract or identifier change | Documentation that changes a contract, requirement or ID |
| Comment and formatting changes | Renames of any kind — **always use `gitnexus_rename`**, never find-and-replace |
| Dependency lock refresh with no version change | Any version change |
| Test additions that touch no production code | Test changes that alter fixtures used by other suites |

Emergency security fixes are **not exempt**. They may compress approval, never the analysis.
</content>
