# JourneyLab — Bug Register

| Field | Value |
| --- | --- |
| Owner | Engineering (unassigned — `BLK-001`) |
| Status | `READY` — **no entries; no code exists to have bugs** |
| Rule | **Every fixed bug gets a regression test.** Check R6 verifies they all still pass at every sub-step |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Implementation log](IMPLEMENTATION_LOG.md) · [Regression log](REGRESSION_LOG.md) · [Incident response](../07-operations/INCIDENT_RESPONSE.md)

---

## Severity

| Level | Definition | Response |
| --- | --- | --- |
| **S1 — Critical** | Wrong plan delivered to a user, cross-tenant exposure, data loss, privacy breach, hard-constraint violation | Stop the line. Incident response. Release halted |
| **S2 — Major** | Core journey broken or materially degraded; citation correctness below gate; provider degradation presented as current data | Fix before the next sub-step proceeds |
| **S3 — Moderate** | Feature defect with a workaround; accessibility defect not blocking task completion | Scheduled within the step |
| **S4 — Minor** | Cosmetic, copy, non-blocking inconsistency | Backlog |

**Any hard-constraint violation is S1 by definition** (`RISK-004`), regardless of how few users saw it. It is the failure mode the product exists to prevent.

---

## Register

| ID | Title | Sev | Found in | Found by | Symptom | Root cause | Fix commit | Regression test | Status | Closed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| — | *No bugs recorded* | | | | | | | | | |

---

## Entry format

```markdown
## BUG-NNN — [Title]

| Field | Value |
| --- | --- |
| Severity | S1–S4 |
| Found during | STEP-NNN.MM / production / review / regression check |
| Found by | |
| Date found | |
| Affected requirements | REQ-… |
| Affected users/tenants | |

### Symptom
What was observed, exactly. Include the correlation ID for production issues.

### Reproduction
Deterministic steps. If non-deterministic, say so and record the frequency.

### Diagnosis
| Hypothesis | Tested how | Result |
| --- | --- | --- |

### Root cause
The actual cause, not the first plausible one. If a wrong hypothesis was
pursued first, record it — the next person will have the same instinct.

### Why existing tests did not catch it
**Required field.** This is the most useful part of the entry.

### Fix
| Field | Value |
| --- | --- |
| Approach | |
| Commit | |
| Blast radius | BR-NNN |
| Sub-step | STEP-NNN.MM |

### Regression test
| Field | Value |
| --- | --- |
| Test ID | TST-… |
| Location | |
| **Proves** | Fails before the fix, passes after |

### Prevention
What changes so this class of bug cannot recur — a lint rule, a contract
constraint, a property-based test, a graph quality check.
```

---

## Rules

1. **A bug is not closed until its regression test exists** and demonstrably fails against the pre-fix code.
2. **Never disable a failing test to go green.** That is itself a bug, logged and escalated.
3. **"Why existing tests did not catch it" is mandatory.** A fix without it repeats.
4. S1 bugs trigger [INCIDENT_RESPONSE](../07-operations/INCIDENT_RESPONSE.md) and a retrospective.
5. Bugs found by the regression cross-check are logged like any other — they are the protocol working, not an embarrassment.
6. A bug caused by a documented assumption being wrong also updates [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md).

---

## Bug classes to watch in this product

Derived from the architecture's known hazards — these are where defects are most likely and most costly:

| Class | Why likely | Guard |
| --- | --- | --- |
| Temporal confusion (observed vs. effective time) | Three time axes; easy to filter on the wrong one | Property-based tests over effective windows |
| Time zone and DST in itinerary arithmetic | Local-time feasibility across boundaries | Golden-set fixtures spanning DST transitions |
| Stale evidence presented as current | Cache and circuit-breaker interaction | `TST-EVID-005`, drills |
| Hard filter bypassed by ranking | Ordering of filter and rank | `TST-CONS-003`, adversarial candidates |
| Protected item mutated by an automated path | Multiple write paths to itinerary items | `TST-CONS-011` |
| Tenant leakage via cache key or job | Tenant context not propagated | `TST-SEC-002` — R7 every sub-step |
| Deletion missing a derived store | Many derived stores | `TST-PRIV-006` traversal proof |
| Model output reaching state without validation | Gateway boundary erosion | `TST-AI-001` |
</content>
