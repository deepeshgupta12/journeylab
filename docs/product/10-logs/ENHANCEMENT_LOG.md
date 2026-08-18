# JourneyLab — Enhancement Log

| Field | Value |
| --- | --- |
| Owner | Product Lead (Deepesh Kumar Gupta) |
| Status | `ACTIVE` — 2 entries, both **`DELIVERED`**: ENH-001 (STEP-004.09), ENH-002 (STEP-001.08) |
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
| ENH-002 | Guard that a carried commitment is discharged | Deepesh Kumar Gupta (during STEP-002.08) | 2026-08-12 | reliability / process | REQ-KG-008 | **ACCEPTED 2026-08-13** (owner) | STEP-001.08 | `DELIVERED` |
| ENH-001 | Detect semantic change by description drift | Deepesh Kumar Gupta (during STEP-004.08) | 2026-08-12 | developer-experience / reliability | REQ-PLAT-008 | **ACCEPTED 2026-08-13** (owner) | STEP-004.09 | `DELIVERED` |

**Status values:** `PROPOSED` · `ACCEPTED` · `SCHEDULED` · `DELIVERED` · `DECLINED` · `DEFERRED`

---

## ENH-004 — Test the data contract's required fields, not just behaviour

| Field | Value |
| --- | --- |
| Proposed by | Deepesh Kumar Gupta, during STEP-005.07 |
| Date | 2026-08-18 |
| Type | reliability / test coverage |
| Status | **PROPOSED** |
| Trigger | **`BUG-027`** — a place record shipped without two of the three fields `DC-EXT-001` marks required, and every test passed |

### Current behavior

`DATA_CONTRACTS.md` states required fields per source: `DC-EXT-001` requires *"stable
ID, coordinates, category"* on a place record, `DC-EXT-003` requires *"stop
coordinates resolvable; service calendar complete"*, and so on. **Nothing reads that
table.** The requirements live in prose and are satisfied by whoever remembers them.

`BUG-027` is what that costs, and the interesting part is how invisible it was. The
adapter did not throw, did not return a wrong value, and passed 36 tests. The
missing fields were an **absence**, and an absence is only visible against the
contract that requires it.

### Proposed change

Parse the required-fields column out of `DATA_CONTRACTS.md` and assert that each
ingestion type carries them — the same shape as `tools/carried_commitments.py`
(`ENH-002`) and the authorization-matrix sync test: a document is the source of
truth and a test reads it.

### Risk

The column is prose (*"Hours must parse to intervals with a time zone"*) and not all
of it is a field list. A parser that silently skips what it cannot understand would
report a green check over the clauses it ignored — which is `RISK-016`'s failure
mode again. It must fail loudly on an unparseable row, and the unparseable rows must
be enumerated rather than skipped.

### Recommendation

**Worth doing, and not urgently.** Four ingestion types exist and the fifth arrives
at STEP-006, so the cost of remembering is still low. It becomes worthwhile at the
point where nobody can hold the table in their head — which is soon, and is
predictable, so it should be scheduled rather than triggered by the next `BUG-027`.

---

## ENH-003 — A place has no location in the public contract

| Field | Value |
| --- | --- |
| Proposed by | Deepesh Kumar Gupta, during STEP-005.07 |
| Date | 2026-08-18 |
| Type | contract gap |
| Status | **PROPOSED** |
| Trigger | Found while fixing `BUG-027`: the internal record now carries a coordinate and the public one still cannot |

### Current behavior

`components.schemas.Place` is `{name, time_zone, place_id}` with
`additionalProperties: false`. `ItineraryItem` has times, cost and evidence, and no
location either. **No schema in `contracts/openapi.yaml` can express where anything
is.**

`REQ-A11Y-003` requires that no core action need the map and that every task
complete with map rendering disabled — which presumes a map exists. It has nothing
to draw. `DC-EXT-001` requires coordinates on the ingested record, so the data will
be there and the contract cannot carry it.

### Proposed change

Add a `GeoPoint` schema and an optional `coordinate` on `Place`. Optional rather
than required, because the API's `Place` is the *published* view and a venue whose
location is licence-restricted must still be returnable.

### Risk

Two, and the second is the one that matters:

1. `Place` is `additionalProperties: false`, so adding a property is a compatible
   change in the response direction and a breaking one in the request direction —
   `.08`'s direction-aware classifier will say which.
2. **A coordinate on a public response is a privacy surface.** `REQ-PRIV-008` and
   `RISK-006` are about location, and `EVENT_CONTRACTS` already bans *"precise
   location"* from event payloads. A venue's coordinate is not a person's, but the
   two become the same thing the moment an itinerary is attributed to a traveller.
   That argument belongs to whoever owns the privacy review, not to this log.

### Recommendation

**Do it before STEP-013 and not in STEP-005.** It is a contract change, it needs the
privacy question answered first, and it is cheap right now — `BASELINE.md` §2:
nothing is released, so a breaking contract change costs nothing today and costs a
major version, a dual-run window and a migration guide after the first release.

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
| Decision | **ACCEPTED and DELIVERED** — owner directive, 2026-08-13 |
| Decided by | Deepesh Kumar Gupta (repository owner) |
| Delivered in | **`STEP-001.08`** (`BR-039`, `IMPL-036`) |
| Outcome against the stated risk | The risk was false positives teaching people to click through. **It fired on its own documentation five times** before the design was right, and each was fixed by an explicit decision rather than a loosened rule: placeholders skipped, a `carry-exempt` marker for prose that describes a carry, and the syntax example written in placeholder form |
| What it found immediately | Six carries pointing at closed sub-steps. Five were genuine discharges needing annotation; **one was a live commitment with no home** — the `auth/errors.py` RFC 9457 migration, carried to `STEP-004.04`, declined there, and never re-carried. `BR-039` §4 <!-- carry-exempt: describes a finding --> |

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
| Outcome | **Delivered in `STEP-004.09`** (`BR-040`, `IMPL-037`). The condition below was met by measurement: **0 findings across 54 described properties**, and that measurement is itself a test so the check degrades loudly rather than quietly. It reports and does not fail the build; the report is consumed at `RELEASE_READINESS_CHECKLIST` §2 |
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
