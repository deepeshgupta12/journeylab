# Runbook — Template

> Copy to `runbooks/RB-XXX-NNN-<slug>.md` and index in [RUNBOOK_INDEX](../07-operations/RUNBOOK_INDEX.md).
> **Write for 3 a.m.** Explicit commands, no assumed context, no "obviously".

---

```markdown
# RB-XXX-NNN — [Runbook title]

| Field | Value |
| --- | --- |
| Owner | *(named role)* |
| Alert(s) | ALRT-… |
| Severity | SEV1 / SEV2 / SEV3 |
| Last rehearsed | YYYY-MM-DD |
| Rehearsal frequency | |

## 1. Trigger
*Exactly what fires this runbook — alert name, condition, threshold, or the
user-report pattern.*

## 2. Scope
*Which services, tenants, regions and data are involved.*

## 3. Customer impact
*What the user experiences right now. Be specific — "degraded" is not an impact
statement. For this product, state whether users may be acting on incorrect
plan data, because that changes the communication obligation.*

## 4. Prerequisites
- Access required:
- Tools required:
- **Do not start without:** *(e.g. a second responder for destructive actions)*

## 5. Diagnosis
> **Diagnose before mitigating.** A runbook that starts with "restart it"
> teaches people to destroy the evidence.

| # | Check | Command / dashboard | Interpretation |
| 1 | | | |

**Decision tree:**
- If X → go to §6.1
- If Y → go to §6.2
- If neither → escalate (§9)

## 6. Safe mitigation
### 6.1 [Scenario A]
1. …
### 6.2 [Scenario B]
1. …

**Destructive actions require:** a second responder, an evidence snapshot, and
a recorded decision.

## 7. Rollback
*How to undo the mitigation if it makes things worse.*

## 8. Verification
- [ ] Alert cleared
- [ ] SLI recovered
- [ ] End-to-end trip trace succeeds
- [ ] No data inconsistency introduced
- [ ] **No stale or fabricated data being served as current**
- [ ] Customer impact ended

## 9. Escalation
| Condition | Escalate to | Channel |
*Named roles and paths — never "escalate if needed".*

## 10. Evidence preservation
*Capture before mitigation where they conflict:*
- Correlation IDs:
- Trip / scenario / evidence-pack IDs:
- Solver config, seed, version:
- Model / prompt / retrieval versions:
- Provider health and quota state:
- Queue and DLQ state:
- Relevant audit events:

**Preserve under production privacy rules** — an incident is not authorisation
to copy personal data into a shared channel.

## 11. Retrospective actions
- [ ] Incident recorded
- [ ] `BUG-NNN` logged with a regression test (check R6)
- [ ] Root cause and *why alerts/tests missed it*
- [ ] This runbook updated
- [ ] Follow-up actions with owners and dates

## 12. Related
*Runbooks, dashboards, alerts, architecture docs.*
```

---

## Quality bar

| Rule | Reason |
| --- | --- |
| Diagnosis before mitigation | Restarting first destroys the evidence |
| Explicit commands | The responder may be unfamiliar with this service |
| Named escalation | "Escalate if needed" means nobody escalates |
| Rehearsed | An unrehearsed runbook is a document, not a capability |
| Rehearsal updates the runbook | The correction is the rehearsal's real output |
| Verification includes data honesty | For this product, recovering while serving stale data as current turns an outage into a correctness incident |
</content>
