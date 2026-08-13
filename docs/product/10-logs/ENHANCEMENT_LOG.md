# JourneyLab — Enhancement Log

| Field | Value |
| --- | --- |
| Owner | Product Lead (Deepesh Kumar Gupta) |
| Status | `ACTIVE` — 2 entries: ENH-001 `SCHEDULED`, ENH-002 awaiting a decision |
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
| ENH-002 | Guard that a carried commitment is discharged | Deepesh Kumar Gupta (during STEP-002.08) | 2026-08-12 | reliability / process | REQ-KG-008 | **PENDING** | — | `PROPOSED` |
| ENH-001 | Detect semantic change by description drift | Deepesh Kumar Gupta (during STEP-004.08) | 2026-08-12 | developer-experience / reliability | REQ-PLAT-008 | **ACCEPTED 2026-08-13** (owner) | STEP-004.09 | `SCHEDULED` |

**Status values:** `PROPOSED` · `ACCEPTED` · `SCHEDULED` · `DELIVERED` · `DECLINED` · `DEFERRED`

---

## ENH-002 — Guard that a carried commitment is discharged

| Field | Value |
| --- | --- |
| Proposed by | Deepesh Kumar Gupta, during STEP-002.08 |
| Date | 2026-08-12 |
| Type | reliability / process |
| Trigger | **`BUG-022`** — a security control was carried from `.05` to `.07`, and `.07` closed `VERIFIED` without it. Nothing failed |

### Current behavior

Sub-step records routinely defer work with a phrase like *"carried to
STEP-002.07"*. `tests/guards/substep-docs.sh` verifies that every `VERIFIED`
sub-step has an implementation, regression and blast-radius record. **It cannot
verify that a promise made in one record was kept in another**, because a carry is
prose.

`BUG-022` is what that costs: server-side session revocation was deferred once,
never picked up, and the gap survived three further sub-steps while `session.ts`
carried a comment asserting the control existed.

### Proposed behavior

Parse `carried to STEP-NNN.MM` (and `carried to STEP-NNN`) out of every sub-step
record. When the named sub-step reaches `VERIFIED`, require that it either
discharges the item or restates it as a carried gap with a new destination. Fail
the build otherwise.

An open carry pointing at a `VERIFIED` sub-step is then a build failure rather than
a thing somebody notices six sub-steps later.

### Value

Directly addresses the only S2 in the register whose root cause is process rather
than code. The register currently shows this failing **once in twenty-two bugs**,
which is a low rate — but its consequence was a security control that everyone
believed existed.

### Cost

Half a day. The parser is straightforward; the real cost is agreeing a shape for
the carry sentence so it can be matched without turning every record into a form.
Free-text carries would need normalising, and there are 26 sub-step records.

### Risk of doing it

**A structured carry is easier to satisfy dishonestly than a prose one.** Once the
guard exists, discharging a carry becomes "make the check pass", and the cheapest
way is to restate it with a new destination — which is exactly what happened here
informally, only now with a green build attesting to it. The guard must count
re-carries and surface them, or it converts a visible failure into a silent one.

### Decision

| Field | Value |
| --- | --- |
| Decision | **PENDING — owner decision required** |
| Decided by | — |
| Rationale | Logged, not built. Building a documentation guard inside a security sub-step is the widening this log exists to prevent, and `ENH-001` was held to the same rule the same week |
| If accepted, sub-step | Its own sub-step under `STEP-001` governance, or fold into `STEP-026` |
| If deferred, revisit at | The next time a carry is written — which is every sub-step, so this should not sit long |

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
| Decision | **ACCEPTED** — owner directive, 2026-08-13 |
| Decided by | Deepesh Kumar Gupta (repository owner) |
| Rationale | Accepted against my own recommendation to defer, which is the owner's call to make. The deferral argument was cost-of-false-positives, not that the gap is acceptable — `CONTRACT_CHANGE_POLICY` §1 calls semantic change the most dangerous category and it has no automated coverage at all |
| Sub-step | **`STEP-004.09`** — reopens STEP-004 from `VERIFIED` 8/8 to 9/9, the same pattern as STEP-003.09 and STEP-002.08 |
| Condition carried from §Risk | **The false-positive rate must be driven near zero before this ships.** A check people learn to acknowledge without reading is worse than no check — this repository already has one degraded signal that reads like a real answer (`gitnexus_query`, `BR-029` §3). That is now an acceptance criterion of `.09`, not a caveat |

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
