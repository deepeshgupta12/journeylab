# Architecture Decision Record — Template

> Copy to `docs/adr/ADR-NNN-<slug>.md` in the code repository, and index it in [DECISION_LOG](../02-delivery/DECISION_LOG.md).
> An ADR records a decision that is **costly to reverse**. Routine choices belong in code review, not here.

---

```markdown
# ADR-NNN — [Decision title]

| Field | Value |
| --- | --- |
| Status | Proposed / Accepted / Superseded by ADR-NNN / Rejected |
| Date | YYYY-MM-DD |
| Owner | *(named person — not a team)* |
| Deciders | |
| Consulted | |
| Scope steps | STEP-NNN |
| Requirements | REQ-… |

## Context
*The forces at play: constraints, requirements, and what makes this decision
necessary now. State facts, not conclusions. If a decision is driven by an
assumption, name the assumption ID.*

## Decision
*What we are doing, stated so someone can tell whether an implementation
complies with it.*

## Options considered
| Option | Pros | Cons | Why not chosen |
| --- | --- | --- | --- |

*A single-option ADR is not a decision — it is a rationalisation. Record the
alternatives honestly, including the one someone will propose again in
six months.*

## Consequences
**Positive:**
**Negative:** *(required — every decision has a cost; an ADR with no negative
consequences is incomplete)*
**Neutral / follow-on:**

## Affected knowledge-graph nodes
| Node | Type | Effect |
*Which services, endpoints, tables, models or prompts this decision constrains.
Obtained from the graph, or marked `BLOCKED` if unavailable.*

## Migration
*How we get from the current state to the decided state, including data and
contract compatibility.*

## Security and privacy implications
| Concern | Effect | Control |

## Operational implications
*Monitoring, alerting, runbooks, on-call burden, cost.*

## Tests
*What proves the decision is implemented and stays implemented — a lint rule,
an architecture test, a contract check.*

## Rollback
*How we reverse this if it proves wrong, and what becomes hard to undo.
"We would rewrite it" is not a rollback plan — say so explicitly if true.*

## Review trigger
*What would cause us to revisit: a measured threshold, a scaling event, a
failed assumption.*
```

---

## Rules

1. **One decision per ADR.** Bundled decisions cannot be superseded independently.
2. **Never edit an accepted ADR's decision.** Supersede it with a new one and link both.
3. **Negative consequences are mandatory.** If none are apparent, the analysis is incomplete.
4. **Name a person as owner**, not a team.
5. **State the review trigger** so the decision has an expiry condition rather than drifting into folklore.
6. Accepted ADRs are indexed in [DECISION_LOG](../02-delivery/DECISION_LOG.md) §1.
</content>
