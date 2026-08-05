# JourneyLab — Work Logs

> **Purpose:** every implementation, bug, fix, enhancement and regression result is recorded here so it can be referred to later. These logs are the project's memory — the place someone goes six months from now to answer "why is this like this?" and "did we already hit this?"

| Field | Value |
| --- | --- |
| Owner | TPM (Deepesh Kumar Gupta) |
| Status | `READY` — logging begins with the first implementation commit |
| Origin | Repository-owner directive, 2026-08-05 |
| Last reviewed | 2026-08-05 |

Navigation: [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md) · [Ways of working](../02-delivery/WAYS_OF_WORKING.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---

## Log inventory

| Log | Records | Written when |
| --- | --- | --- |
| [IMPLEMENTATION_LOG](IMPLEMENTATION_LOG.md) | What was built, why, and the decisions taken inside the work | Every sub-step |
| [BUG_REGISTER](BUG_REGISTER.md) | Every bug — found, diagnosed, fixed, with its regression test | On discovery and on fix |
| [ENHANCEMENT_LOG](ENHANCEMENT_LOG.md) | Improvements beyond the stated requirement | When proposed and when delivered |
| [REGRESSION_LOG](REGRESSION_LOG.md) | R1–R7 cross-check results per sub-step | Every sub-step |
| `blast-radius/` | One `BR-NNN` assessment per change | Before every change |

---

## Why these are separate from the changelog

| Artifact | Audience | Question it answers |
| --- | --- | --- |
| [CHANGELOG](../02-delivery/CHANGELOG.md) | Everyone, per release | "What changed in this release?" |
| **IMPLEMENTATION_LOG** | Engineers, later | "How and why was this built this way?" |
| **BUG_REGISTER** | Engineers, later | "Have we seen this before, and what fixed it?" |
| **REGRESSION_LOG** | Reviewers, auditors | "Was anything verified before this shipped?" |
| Git history | Engineers | "What lines changed?" |

Git history says what changed. These logs say **what it cost to learn**, which is the part that is otherwise lost.

---

## Logging rules

1. **Log at the time, not afterwards.** A log written from memory at release time is fiction.
2. **One entry per sub-step**, written in the same commit as the work.
3. **Record the failure, not only the fix.** The symptom, the wrong hypothesis and the actual cause are the valuable parts.
4. **Every bug fix gets a regression test**, referenced in the register and enforced by check R6.
5. **Never delete an entry.** Corrections are new entries referencing the old one.
6. **Link identifiers** — `STEP-NNN.MM`, `REQ-*`, `BR-NNN`, `BUG-NNN`, `TST-*`, commit SHA.
7. **No AI attribution** in any log entry or commit (`ADR-006`).

---

## ID allocation

| Prefix | Range | Allocated by |
| --- | --- | --- |
| `BUG-NNN` | 001+ | Next free number in the register |
| `ENH-NNN` | 001+ | Next free number in the enhancement log |
| `BR-NNN` | 001+ | Next free number in `blast-radius/` |
| `IMPL-NNN` | 001+ | Next free number in the implementation log |

Numbers are never reused, including for dropped or rejected items.
