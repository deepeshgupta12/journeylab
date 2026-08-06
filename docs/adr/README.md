# Architecture Decision Records

Full ADRs for every accepted decision. The canonical **index** — including open and
deferred decisions — is
[DECISION_LOG](../product/02-delivery/DECISION_LOG.md).

## Naming

Files are `ADR-NNN-<slug>.md`, matching the numbering already established in the
decision log.

> **Deviation from `STEP-001` §18**, recorded deliberately: that step listed
> `docs/adr/0001-architecture.md`, a filename written before ADRs were numbered.
> `ADR-001` is "documentation is the source of truth"; the architecture decision is
> **`ADR-003`**. Renumbering to match the suggested filename would break
> cross-references across roughly 100 documents and invalidate commit messages
> citing ADRs. See `BR-005`.

## Accepted

| ADR | Decision | Status |
| --- | --- | --- |
| [ADR-001](ADR-001-documentation-source-of-truth.md) | Documentation is the source of truth before code exists | Accepted |
| [ADR-002](ADR-002-deterministic-engines-own-feasibility.md) | Deterministic engines own feasibility; the LLM owns language | Accepted |
| [ADR-003](ADR-003-modular-monolith-and-workers.md) | Modular monolith plus isolated compute workers for the MVP | Accepted |
| [ADR-004](ADR-004-immutable-evidence-packs.md) | Immutable evidence packs as solver input | Accepted |
| [ADR-005](ADR-005-gitnexus-knowledge-graph.md) | GitNexus is the knowledge-graph toolchain | Accepted |
| [ADR-006](ADR-006-no-ai-commit-attribution.md) | Commit messages carry no AI co-authorship attribution | Accepted |
| [ADR-007](ADR-007-just-in-time-decisions.md) | Decisions are resolved just-in-time at the step that needs them | Accepted |
| [ADR-008](ADR-008-just-ahead-of-need-sub-steps.md) | Sub-step files are written just-ahead-of-need | Accepted |
| [ADR-009](ADR-009-typescript-7.md) | TypeScript 7.0.2 supersedes the documented 6.0 baseline | Accepted |
| [ADR-010](ADR-010-repository-ownership.md) | Repository ownership assigned to a single accountable owner | Accepted |
| [ADR-011](ADR-011-psycopg3-as-the-postgres-driver.md) | psycopg 3 is the PostgreSQL driver; no ORM adopted yet | Accepted |
| [ADR-012](ADR-012-authorization-policy-in-python.md) | Authorization policy is Python, co-located with enforcement | Accepted |

## Rules

1. **One decision per ADR** — bundled decisions cannot be superseded independently.
2. **Never edit an accepted ADR's decision.** Supersede it and link both.
3. **Negative consequences are mandatory.** An ADR with none is incomplete.
4. **Name a person as owner**, not a team.
5. State a **review trigger**, so a decision has an expiry condition rather than
   drifting into folklore.

New ADRs use [ADR_TEMPLATE](../product/09-templates/ADR_TEMPLATE.md).
