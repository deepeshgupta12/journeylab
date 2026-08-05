# JourneyLab — Implementation Log

| Field | Value |
| --- | --- |
| Owner | Implementing engineer per entry |
| Status | `READY` — **no entries yet; no implementation has occurred** |
| Cadence | One entry per sub-step, written in the same commit as the work |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Bug register](BUG_REGISTER.md) · [Regression log](REGRESSION_LOG.md) · [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md)

---

## Entry format

```markdown
## IMPL-NNN — STEP-NNN.MM — [Sub-step title]

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Author | |
| Requirements | REQ-… |
| Blast radius | BR-NNN (LOW/MEDIUM/HIGH/CRITICAL) |
| Commit | `<sha>` |
| Graph indexed commit | `<sha>` — matched HEAD? yes/no |

### What was built
Concrete description of the delivered behavior.

### Why this approach
The options considered and why this one. **If an obvious simpler approach was
rejected, say why** — this is the field future readers actually need.

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |

### Deviations from the step file
What differed from the plan, and why. If none, say "none".

### What surprised us
Anything that behaved differently from expectation. This is where the
expensive knowledge lives.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |

### Verification
| Check | Result |
| --- | --- |
| Sub-step tests | |
| Regression R1–R7 | see REGRESSION_LOG |
| detect_changes() scope | |
| Documentation updated | |
```

---

## Entries

*No entries. Implementation has not begun — `BLK-002` (no application code) and `BLK-001` (no assigned owners).*

The first entry will be `IMPL-001` for `STEP-001.01`.

---

## What must be logged

| Event | Log here | Also log |
| --- | --- | --- |
| Sub-step implemented | ✅ | Regression log, tracker |
| Bug found during implementation | Reference it | [BUG_REGISTER](BUG_REGISTER.md) |
| Bug fixed | Reference it | [BUG_REGISTER](BUG_REGISTER.md) + regression test |
| Enhancement beyond requirement | Reference it | [ENHANCEMENT_LOG](ENHANCEMENT_LOG.md) |
| Architectural decision taken mid-work | ✅ + promote | [DECISION_LOG](../02-delivery/DECISION_LOG.md) as an ADR |
| Assumption invalidated | ✅ | [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md) |
| Approach abandoned | ✅ **with the reason** | Sub-step marked `DROPPED` |
| Dependency or version change | ✅ | Blast-radius record |

**Negative results are recorded, not discarded** (portfolio standard §7.38). An approach that failed and why is more valuable to the next engineer than a clean history that hides it.
</content>
