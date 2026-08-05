# JourneyLab — Codebase Knowledge Graph

| Field | Value |
| --- | --- |
| Owner | Platform (Deepesh Kumar Gupta) |
| Status | **Operational but not yet load-bearing** — indexed 2026-08-05; contains documentation only |
| Tool | GitNexus (`ADR-005`) |
| Last reviewed | 2026-08-05 |

Navigation: [Schema](KNOWLEDGE_GRAPH_SCHEMA.md) · [Indexing & refresh](INDEXING_AND_REFRESH.md) · [Change impact protocol](CHANGE_IMPACT_PROTOCOL.md) · [Query playbook](GRAPH_QUERY_PLAYBOOK.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Purpose

The code graph answers questions that source search cannot:

- What breaks if I change this symbol — including through an API, event, table, prompt or test?
- Which requirement does this code serve, and is that requirement tested?
- Who owns this, and which runbook covers it in production?
- Which production services and customer workflows does this change touch?
- What is the complete evidence path from a product output back to source data?

**What it is not:** a replacement for source control or the transactional database. It is derived, rebuildable, and never authoritative for business state.

---

## 2. Verified current state

| Fact | Value |
| --- | --- |
| Indexed | 2026-08-05 |
| Size | **~1,860 nodes, ~2,535 edges**, 0 clusters, 0 execution flows |
| Content | Markdown documentation files and their relationships |
| Application symbols | **Zero** — no source code exists |
| Freshness | `npx gitnexus status` → up to date |

**Honest assessment:** at ~1,860 nodes covering documentation, this graph currently proves the *pipeline works*. It cannot yet answer a single impact question about application behavior, because there is no application. Impact analysis is `BLOCKED` and the static fallback applies (`RISK-014`, `ASM-025`).

The value of indexing now rather than later: the first source commit gets a working, already-configured graph and a pre-change discipline that is habitual rather than retrofitted.

---

## 3. What gets indexed once code exists

| Source | Extracted into |
| --- | --- |
| TypeScript/Python source | `File`, `Module`, `Class`, `Function`, `Method`, `Type`, `Constant` + `CALLS`, `IMPORTS`, `IMPLEMENTS` |
| `contracts/openapi.yaml` | `APIEndpoint`, `Schema` + `EXPOSES` |
| `contracts/asyncapi.yaml` | `Event`, `Topic` + `PUBLISHES`, `CONSUMES` |
| `db/migrations/` | `Table`, `Column`, `Index`, `Migration` + `READS`, `WRITES`, `MIGRATES` |
| `ml/registry/`, `ml/training/` | `Model`, `Feature`, `TrainingRun`, `EvaluationDataset`, `Metric` |
| `services/ai/src/prompts/`, `tools/`, `guardrails.py` | `Prompt`, `Tool`, `Guardrail`, `Retriever` |
| `tests/` | `TestCase` + `TESTED_BY` |
| `docs/product/` requirement IDs | `Requirement`, `ScopeStep` + `IMPLEMENTS_REQUIREMENT` |
| `infra/`, `deploy/`, `.github/workflows/` | `Service`, `Deployment`, `Environment`, `InfrastructureResource` |
| `observability/` | `Dashboard`, `Alert` + `OBSERVED_BY`, `ALERTED_BY` |
| `runbooks/` | `Runbook` + `RECOVERED_BY` |
| Git history | `Commit`, `PullRequest`, `Owner` + `CHANGED_IN`, `OWNED_BY` |
| OTel runtime data | `OBSERVED_BY` edges from route templates, SQL fingerprints, topic names, model traces |

**Runtime joins never store customer payloads** — only route templates, fingerprints and topic names.

---

## 4. Available tooling

| Capability | GitNexus tool |
| --- | --- |
| Impact / blast radius | `mcp__gitnexus__impact` (`direction: upstream \| downstream`) |
| Full symbol context | `mcp__gitnexus__context` |
| Concept search over execution flows | `mcp__gitnexus__query` |
| Pre-commit scope verification | `mcp__gitnexus__detect_changes` |
| Safe rename across the call graph | `mcp__gitnexus__rename` |
| Arbitrary graph query | `mcp__gitnexus__cypher` |
| Control/data dependence | `mcp__gitnexus__pdg_query` |
| Source→sink data flow | `mcp__gitnexus__trace` |
| API surface impact | `mcp__gitnexus__api_impact` |
| Route and tool inventories | `mcp__gitnexus__route_map`, `mcp__gitnexus__tool_map` |
| Structural checks (import cycles) | `mcp__gitnexus__check` |
| Explanation of a flow | `mcp__gitnexus__explain` |

Resources: `gitnexus://repo/journeylab/{context,clusters,processes,process/{name}}`.

---

## 5. Mandatory working rules

These are enforced repository rules, restated in `CLAUDE.md`:

1. **Run impact analysis before editing any symbol** and report the blast radius before proceeding.
2. **Run `detect_changes()` before committing** to confirm only the expected scope changed.
3. **Warn on HIGH or CRITICAL risk** and obtain owner approval before continuing.
4. **Never rename with find-and-replace** — use `gitnexus_rename`, which understands the call graph.
5. **Never proceed on a stale index** — refresh first.
6. **Never claim the graph was queried when it was not** — if it is unavailable, say `BLOCKED` and apply the static fallback.

---

## 6. Use and misuse

| Legitimate use | Not a use |
| --- | --- |
| Change impact and blast radius | Source of truth for business state |
| Ownership and coverage gaps | Replacement for code review |
| Incident diagnosis (symbol → service → alert → runbook) | Replacement for observability |
| Evidence-backed GraphRAG for engineering questions | Answering end-user product questions (that is the domain graph) |
| Release gating on precision-verified impact results | Gating on unverified inferred edges |

**Precision precondition:** sampled call and dependency edges must meet the agreed precision threshold **before** impact results are used as a release blocker (`REQ-KG-003` family). Blocking releases on unvalidated inferred edges trains people to override the gate, which destroys it.

---

## 7. Permissions

| Rule | Detail |
| --- | --- |
| Repository scope | Source content follows repository permissions; a caller cannot see a path they cannot inspect at source (`REQ-KG-006`) |
| No secrets | Secrets, customer payloads and restricted code never enter graph properties or embeddings (`REQ-KG-007`) |
| Audit | Every graph answer is logged with its traversed evidence |
| Separation | Repository access confers **no** access to the tenant-scoped domain graph |

---

## 8. Gaps to close when code lands

| Gap | Action | Owner |
| --- | --- | --- |
| Zero application symbols | Re-index after the first source merge | Platform |
| Coverage gates unevaluated | Evaluate `REQ-KG-001`/`REQ-KG-002` for the first time | Platform |
| No CI refresh | Add `.github/workflows/knowledge-graph.yml` in `STEP-026` | Platform |
| No release graph tagging | Add to the release procedure in `STEP-027` | SRE |
| Edge precision unmeasured | Sample and measure before enabling the release gate | Platform |
| Requirement linkage untested | Verify `IMPLEMENTS_REQUIREMENT` edges resolve from `docs/product/` IDs | TPM |
