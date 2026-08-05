# JourneyLab — Graph Quality and Governance

| Field | Value |
| --- | --- |
| Owner | Platform (unassigned — `BLK-001`) |
| Status | `READY` — gates defined; **most not yet evaluable** (no source code) |
| Last reviewed | 2026-08-05 |

Navigation: [Indexing & refresh](INDEXING_AND_REFRESH.md) · [Code graph](CODEBASE_KNOWLEDGE_GRAPH.md) · [Query playbook](GRAPH_QUERY_PLAYBOOK.md) · [Release readiness](../06-quality/RELEASE_READINESS_CHECKLIST.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Quality gates

| ID | Gate | Target | Current | Enforcement |
| --- | --- | --- | --- | --- |
| KG-001 | First-party source files parsed | ≥ 95% | **Not evaluable** — no source | CI blocks release below target |
| KG-002 | Public symbols linked to an owner or parent module | ≥ 90% | Not evaluable | CI warns; blocks at release |
| KG-003 | Default-branch refresh after merge | ≤ 10 min | Not implemented (no CI) | `ALRT-KG-001` |
| KG-004 | Release graph immutable and tagged | Required | Not implemented | Release procedure |
| KG-005 | Sampled call/dependency edge precision | Agreed threshold, measured | Not evaluable | **Blocks using impact results as a release gate** |
| KG-006 | No unowned public API, event, migration, model or production service | Zero | Not evaluable | CI blocks |
| KG-007 | Extraction gaps and exclusions visible | Required | Partially met — `status` reports coverage | Coverage report |
| KG-008 | Provenance on every node and inferred edge | 100% | Enforced by extractor | Schema constraint |
| KG-009 | No secrets, customer payloads or restricted code in properties or embeddings | Zero | Met — embeddings disabled | Scan before enabling embeddings |
| KG-010 | Untested requirements | Not increasing | Not evaluable | Sub-step regression check R4 |
| KG-011 | Orphan/unowned nodes | Not increasing | Not evaluable | Sub-step regression check R5 |
| KG-012 | Import cycles between modules | Zero | Not evaluable | `gitnexus check` in CI |

**KG-005 is the gate that protects the others.** Until edge precision is measured, impact results inform judgement but must not block a release — a gate people learn to override is worse than no gate.

---

## 2. Coverage accounting

Coverage must distinguish three different things, because reporting them as one number hides the problem:

| Category | Counted as | Why |
| --- | --- | --- |
| Parsed successfully | ✅ covered | Real coverage |
| **Deliberately excluded** (generated clients, vendored code, `node_modules`) | ➖ excluded, listed explicitly | Legitimate, but must be visible |
| **Failed to parse** | ❌ gap, alerted | A silent parse failure looks identical to "no dependencies" and is the most dangerous state |

A file that fails to parse is never counted as excluded.

---

## 3. Inferred edges and human correction

| Rule | Detail |
| --- | --- |
| Exact first | Identifier matches produce edges with confidence 1.0 |
| Semantic second | Reviewed semantic matches are **inferred edges**, carrying `inference_method`, `evidence` and confidence < 1.0 |
| Visibility | Inferred edges are visually distinct in the explorer and in query results |
| Correction | Developers can confirm or reject an inferred edge |
| **Corrections become tests** | Every reviewed correction becomes an extractor regression test (`REQ-KG-005`) so the same mistake cannot recur |
| Precision sampling | Random samples of inferred edges are audited; the measured precision is the KG-005 input |

---

## 4. Security and permissions

| Control | Rule |
| --- | --- |
| Repository scope | Graph traversal respects repository permissions |
| Tenant scope | Domain-graph traversal filters by tenant **during** traversal |
| No leakage by inference | Counts, path lengths and timing must not reveal inaccessible nodes |
| No secrets | Secrets, customer payloads and restricted code never enter properties or embeddings (`REQ-KG-007`) |
| Embeddings | **Disabled by default.** Enabling requires a documented scan proving no sensitive content is embedded |
| Audit | Every graph answer logged with traversed evidence, caller and indexed commit |
| Separation | Code-graph access grants no domain-graph access |

---

## 5. Ownership

| Artifact | Owner |
| --- | --- |
| Extractors and loaders | Platform |
| Code-graph quality gates | Platform |
| Domain-graph schema | Data Architect |
| Domain-graph queries used in product features | Owning feature team |
| Graph refresh CI | Platform |
| Release graph tagging | SRE |
| Correction review | Owning code area |

---

## 6. Governance rules

1. The graph is **derived, never authoritative**. A graph/database disagreement is resolved in favour of the database and raised as a defect.
2. The graph does **not replace** source control, the transactional database, code review or observability.
3. **Never claim the graph was queried when it was not.** `BLOCKED` is an acceptable state; a fabricated result is not.
4. Impact results become a release blocker only after KG-005 precision is measured.
5. Extraction gaps are surfaced in the release readiness review, not buried in a dashboard.
6. Graph changes follow the same change-impact discipline as code — an extractor change alters every downstream answer.

---

## 7. Honest current assessment

| Question | Answer |
| --- | --- |
| Is the graph installed and working? | **Yes** — verified 2026-08-05 |
| Does it index this repository? | **Yes** — ~1,860 nodes, ~2,535 edges |
| Does it cover application code? | **No — none exists** |
| Can it answer impact questions about product behavior? | **No** |
| Do the quality gates pass? | **Not evaluable** — they have no subject |
| Is the pre-change protocol satisfied for code changes? | **No — `BLOCKED`**, static fallback applies |
| What single action changes this? | The first source-code merge, followed immediately by `npx gitnexus analyze` |

Reporting this as "knowledge graph: complete ✅" would be false. It is: **pipeline operational, coverage pending code** (`RISK-014`).
