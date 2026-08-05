# JourneyLab — Enhancement Log

| Field | Value |
| --- | --- |
| Owner | Product Lead (unassigned — `BLK-001`) |
| Status | `READY` — no entries yet |
| Purpose | Record improvements proposed or delivered beyond the stated requirement, so scope growth is visible rather than silent |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Implementation log](IMPLEMENTATION_LOG.md) · [Out of scope](../01-product/OUT_OF_SCOPE.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md)

---

## Why enhancements are logged separately

An enhancement is work nobody asked for. It may be excellent and it may be scope creep, and the difference is only visible if it is recorded rather than absorbed into a commit. Logging it makes three things possible: the owner can accept or decline it, its cost is attributable, and a good idea arriving at the wrong time is not lost.

**Rule: an enhancement is never implemented silently inside another sub-step.** It is logged, then either scheduled as its own sub-step or declined.

---

## Register

| ID | Title | Proposed by | Date | Type | Requirement affected | Decision | Delivered in | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| — | *No entries* | | | | | | | |

**Status values:** `PROPOSED` · `ACCEPTED` · `SCHEDULED` · `DELIVERED` · `DECLINED` · `DEFERRED`

---

## Entry format

```markdown
## ENH-NNN — [Title]

| Field | Value |
| --- | --- |
| Proposed by | |
| Date | |
| Type | UX / performance / reliability / developer-experience / accessibility / cost |
| Trigger | What prompted it — a bug, a review comment, an observation during implementation |

### Current behavior
What happens today, and why that is acceptable-but-improvable.

### Proposed behavior
Concrete. Not "make it better".

### Value
Which KPI, requirement or risk this improves, and by roughly how much.

### Cost
Effort, added surface area, new dependency, ongoing maintenance.

### Risk of doing it
Especially: does it add a code path that must now be tested, monitored and
deleted from? Every enhancement has a permanent tail.

### Decision
| Field | Value |
| --- | --- |
| Decision | ACCEPTED / DECLINED / DEFERRED |
| Decided by | |
| Rationale | |
| If accepted, sub-step | STEP-NNN.MM |
| If deferred, revisit at | |
```

---

## Rules

1. **Log before implementing.** An enhancement discovered mid-sub-step is logged and deferred to its own sub-step unless it is trivial and directly required to complete the current work.
2. **A declined enhancement stays in the log** with its rationale — the same idea will be proposed again.
3. Enhancements that change a requirement update [FUNCTIONAL_REQUIREMENTS](../01-product/FUNCTIONAL_REQUIREMENTS.md) and the traceability matrix.
4. Enhancements that change scope boundaries update [OUT_OF_SCOPE](../01-product/OUT_OF_SCOPE.md).
5. An enhancement affecting a KPI must not breach that KPI's guardrail — check [SUCCESS_METRICS](../01-product/SUCCESS_METRICS.md) before accepting.

---

## Enhancement anti-patterns for this product

| Anti-pattern | Why it is dangerous here |
| --- | --- |
| "Let the model handle this edge case" | Erodes `ADR-002`; feasibility must stay deterministic |
| "Cache it longer to reduce cost" | May breach provider licence terms and freshness SLOs |
| "Skip the citation for this field" | Directly attacks the product's trust mechanism (`REQ-EVID-004`) |
| "Add one more scenario objective" | Increases solver latency against `REQ-NFR-004`; diversity, not count, is the goal |
| "Auto-apply obviously-safe replans" | Violates the user-control principle (`EXC-004`) — no replan is obviously safe to the person travelling |
| "Store location to make the live view faster" | Breaches `REQ-PRIV-008` and increases `RISK-006` |
</content>
