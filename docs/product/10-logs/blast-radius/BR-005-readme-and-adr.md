# BR-005 — README, architecture map and ADR files

| Field | Value |
| --- | --- |
| Sub-step | STEP-001.05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-004 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-05 |

## 1. Intent
A new engineer orients and runs the project from `README.md` alone, and the accepted architecture decisions exist as reviewable ADR files rather than only as decision-log entries.

## 2. Graph state (protocol step 2)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `23ec095` |
| Graph indexed commit | `23ec095` |
| **Match?** | **Yes** — verified before starting |
| Status | **`BLOCKED` for application code — static fallback** |

## 3. Target nodes
Documentation only: `README.md` (new), `docs/adr/` (new directory).

## 4. Dependencies
**Inbound:** none — no code imports documentation.
**Outbound:** README references commands and ports established in STEP-001.01–.04. If those drift, the README lies — mitigated by the executable guard in §7.

## 5. Impact by category
| Category | Affected | Confidence |
| --- | --- | --- |
| Documentation | `README.md`, `docs/adr/*` (10 files), `DECISION_LOG` index | High |
| Tests | New `readme-commands.sh` guard | High |
| Code / contracts / data / infra | **None** | High |

## 6. Naming conflict found and resolved
`STEP-001` §18 lists `docs/adr/0001-architecture.md` — a filename written before ADRs were numbered. But `DECISION_LOG` already establishes `ADR-001` as *"Documentation is the source of truth"*; the architecture decision is **`ADR-003`** (modular monolith).

**Resolution:** keep the established `ADR-001`…`ADR-010` numbering and name files `ADR-NNN-<slug>.md`. Renumbering to satisfy the blueprint's suggested filename would break cross-references in roughly 100 documents and invalidate every commit message citing an ADR.

**Recorded as a deliberate deviation from the step file, not an oversight.** The step file's §18 is updated to match.

## 7. The acceptance criterion I cannot fully satisfy
The sub-step requires: *"an engineer who did not write the README completes setup using it alone."* I am the author, so I cannot honestly self-certify that.

**What I can do instead, and did:** an executable guard (`tests/guards/readme-commands.sh`) that extracts the documented setup commands and runs them, proving they are **correct and current**. That verifies the commands work; it does **not** verify they are *comprehensible to a newcomer*.

The criterion is therefore recorded as **partially satisfied**, with the human half outstanding. Claiming otherwise would be exactly the false-pass pattern seen three times already in this repository.

## 8. Risk
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 1 | Documentation only; no executable path changes |
| Severity | 2 | A wrong README wastes a newcomer's first hour |
| Reach | 1 | No users or services |
| Detectability | 1 | Guard executes the documented commands |
| Reversibility | 1 | `git revert` |
| **Confidence** | 2 | Exhaustive: no code exists to be affected |
| Customer criticality | 1 | None |

**Overall: LOW**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| README comprehensibility to a newcomer | Author cannot self-assess | **Open** — needs a second person; recorded, not claimed |
| Node 24 PATH persistence | Homebrew keg-only install is not on PATH by default | Documented explicitly in the README with the export line |

## 10. Required actions
Write README; create ADR files; index them; add the executable README guard; update `STEP-001` §18 for the naming deviation.

## 11. Approval
Owner instructed to proceed. Risk LOW — no additional approval required.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | Documentation + 1 guard; no symbols |
| Regression R1–R7 | **PASS** — R1 initially FAILED on `guard:substep-docs` (BUG-003 guard caught a live recurrence); records written, re-run green |

## 13. Disposition
**Merged.** ADR naming deviation recorded and step file corrected. README acceptance criterion recorded as **partial** — commands proven by execution; newcomer comprehensibility outstanding.
