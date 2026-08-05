# ADR-005 — GitNexus is the knowledge-graph toolchain

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Platform · **Status:** Accepted
- **Context:** `KNOWLEDGE_GRAPH_TOOL` was `AUTO_DISCOVER`. GitNexus was verified present and functional, with an MCP server and CLI.
- **Decision:** GitNexus provides the codebase knowledge graph, pre-change impact analysis and change detection. The **product domain graph is a separate concern** and is not served by GitNexus; it is specified in [DOMAIN_KNOWLEDGE_GRAPH](../05-knowledge-graph/DOMAIN_KNOWLEDGE_GRAPH.md) as a Neo4j/PostgreSQL design to be built in `STEP-026`.
- **Verified evidence:** `npx gitnexus analyze` succeeded on 2026-08-05 — ~1,860 nodes, ~2,535 edges; `npx gitnexus status` reports the index up to date. **The index currently covers Markdown documentation only, because no source code exists.**
- **Consequences:** `npx gitnexus <command>` is the documented invocation (the project-local `run.cjs` runner was not generated — see `ASM-009`). Graph coverage gates in `REQ-KG-001` cannot be meaningfully evaluated until code lands.
- **Alternatives rejected:** Hand-maintained dependency documentation (drifts immediately); deferring graph tooling until code exists (would let the first commits merge without impact analysis).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
