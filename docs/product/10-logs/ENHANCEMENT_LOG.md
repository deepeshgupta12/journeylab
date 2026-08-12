# JourneyLab — Enhancement Log

| Field | Value |
| --- | --- |
| Owner | Product Lead (Deepesh Kumar Gupta) |
| Status | `ACTIVE` — 1 entry, awaiting an owner decision |
| Purpose | Record improvements proposed or delivered beyond the stated requirement, so scope growth is visible rather than silent |
| Last reviewed | 2026-08-12 |

Navigation: [Logs index](README.md) · [Implementation log](IMPLEMENTATION_LOG.md) · [Out of scope](../01-product/OUT_OF_SCOPE.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md)

---

## Why enhancements are logged separately

An enhancement is work nobody asked for. It may be excellent and it may be scope creep, and the difference is only visible if it is recorded rather than absorbed into a commit. Logging it makes three things possible: the owner can accept or decline it, its cost is attributable, and a good idea arriving at the wrong time is not lost.

**Rule: an enhancement is never implemented silently inside another sub-step.** It is logged, then either scheduled as its own sub-step or declined.

---

## Register

| ID | Title | Proposed by | Date | Type | Requirement affected | Decision | Delivered in | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENH-001 | Detect semantic change by description drift | Deepesh Kumar Gupta (during STEP-004.08) | 2026-08-12 | developer-experience / reliability | REQ-PLAT-008 | **PENDING** | — | `PROPOSED` |

**Status values:** `PROPOSED` · `ACCEPTED` · `SCHEDULED` · `DELIVERED` · `DECLINED` · `DEFERRED`

---

## ENH-001 — Detect semantic change by description drift

| Field | Value |
| --- | --- |
| Proposed by | Deepesh Kumar Gupta, during STEP-004.08 |
| Date | 2026-08-12 |
| Type | reliability / developer-experience |
| Trigger | Writing `tools/contract_diff.py` and having to document, in the module docstring, that the most dangerous class of change is the one it cannot see |

### Current behavior

`CONTRACT_CHANGE_POLICY` §1: *"Changing what a field means while keeping its name
and type passes every automated compatibility check and breaks every consumer. It
is always treated as breaking."*

The classifier delivered in STEP-004.08 is structural. A field that keeps its name,
type and required-ness while changing meaning is invisible to it, and the sub-step
record for `.08` says as much rather than implying otherwise. Today the only
control is review.

That is acceptable because it is honest and because nothing is released yet. It is
improvable because review is exactly what stops happening under delivery pressure,
which is when a semantic change is most likely to be made.

### Proposed behavior

Hash each schema property's `description` alongside its structure. When a property
is structurally identical between baseline and current but its **description
changed**, emit `REVIEW_REQUIRED` naming both texts.

Not a new severity class in the gate — a report the author must acknowledge.

The insight is that a semantic change is undetectable in general, but a **documented**
semantic change is not: an author who changes what a field means and updates its
description has left a machine-readable trace. The check converts "invisible" into
"invisible only when undocumented", which is a strictly smaller hole.

### Value

Addresses the category `CONTRACT_CHANGE_POLICY` §1 calls the most dangerous, and
which `REQ-PLAT-008` currently has no automated coverage for at all. Cheap: the
diff already walks every property.

### Cost

Roughly a day. Its real cost is false positives — a typo fix in a description would
trip it, and a check that fires on prose edits is one people learn to acknowledge
without reading, which would leave us worse off than having no check.

Mitigating that means normalising whitespace, ignoring pure-markdown edits, and
probably a `# semantic: unchanged` escape hatch — and an escape hatch is a permanent
maintenance surface with its own failure mode.

### Risk of doing it

**The honest risk is that it teaches people to click through a warning.** This
repository already has one degraded signal that reads as a real answer
(`gitnexus_query` returning empty, `BR-029` §3), and the lesson there was that a
check nobody can trust is worse than a check nobody has. If the false-positive rate
is not driven near zero first, this should not ship.

### Decision

| Field | Value |
| --- | --- |
| Decision | **PENDING — owner decision required** |
| Decided by | — |
| Rationale | Logged rather than implemented, per this log's rule 1. It is not required by `REQ-PLAT-008` and the `.08` sub-step record explicitly scopes semantic change to review |
| If accepted, sub-step | Suggest `STEP-004.09`, or fold into `STEP-026` alongside the graph work |
| If deferred, revisit at | Before the first external consumer integrates (`STEP-016`) — after that a semantic change is expensive rather than free |

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
