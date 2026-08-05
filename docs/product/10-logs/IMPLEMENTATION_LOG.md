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

## IMPL-001 — STEP-001.01 — Workspace skeleton and pinned toolchain

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Blast radius | BR-001 (LOW) |
| Graph indexed commit | `c37d106` — matched HEAD at pre-change |

### What was built
pnpm workspace (`package.json`, `pnpm-workspace.yaml`) and uv Python workspace
(`pyproject.toml`), version pins (`.nvmrc` 24, `.python-version` 3.14), workspace
directories (`apps/`, `packages/`, `services/`, `tests/`) with boundary READMEs,
and both lock files generated.

### Why this approach
Two toolchain decisions were escalated to the repository owner under `ADR-007`
(propose, then confirm), because the environment did not match the documented plan:

| Decision | Environment finding | Owner choice |
| --- | --- | --- |
| Package manager | pnpm absent, corepack unavailable | **Install pnpm globally** (over npm workspaces) |
| Node runtime | local v25.9.0 vs. Node 24 LTS baseline | **Install Node 24 locally** (over adopting 25) |

Both preserve the blueprint baseline rather than bending it to the machine, which
keeps `ASM-004` honest.

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |
| Ruff `DTZ` rule enabled | Default rule set | Flags naive datetimes. This product has three time axes; a naive datetime becomes an infeasible itinerary in STEP-012 | No — captured in `pyproject.toml` comment |
| Placeholder scripts exit 0 with a `[STEP-001.02]` marker | Omit scripts entirely | `pnpm verify` is runnable from day one; markers make the gap visible rather than silent | No |
| pytest markers for `security`/`contract`/`property` | Add later | R7 and R2 need selectable suites from the first test | No |

### Deviations from the step file
None in scope. The step file assumed pnpm and Node 24 were present; both had to be
installed first. Recorded as environment facts, not scope change.

### What surprised us
Two things, both instructive:

1. **`pnpm install` was the first thing in this repository that actually executed
   anything** — and it immediately found `BUG-001`, a defect present in 110 files
   for hours. Markdown had silently absorbed it.
2. **The regression guard reproduced the bug inside itself.** Embedding the literal
   offending pattern truncated the guard's own source file. Fixed by assembling the
   pattern at runtime; the failure mode is now documented in the guard's header so
   nobody "simplifies" it back.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |
| Stray-markup guard | Regression test | `tests/guards/no-stray-markup.sh` |
| Lock-file drift CI enforcement | Deferred | STEP-001.03 |
| Node 24 PATH is not persistent (keg-only brew install) | Documentation | STEP-001.05 README |

### Verification
| Check | Result |
| --- | --- |
| `pnpm install` under Node 24.19.0 | PASS — `pnpm-lock.yaml` created |
| `uv sync` | PASS — Python 3.14.2 resolved, `uv.lock` created |
| `pnpm verify` | PASS |
| Regression R1–R7 | See REGRESSION_LOG |

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
