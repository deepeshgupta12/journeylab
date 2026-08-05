# BR-006 — CI workflows and the change-impact merge gate

| Field | Value |
| --- | --- |
| Sub-step | STEP-001.06 |
| Requirements | REQ-KG-003, REQ-KG-008 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-05 |

## 1. Intent
Make `REQ-KG-008` **enforceable rather than procedural**: a change must not merge without a completed change-impact record. Plus incremental graph refresh on merge (`REQ-KG-003`) and an index/HEAD divergence check.

This is the sub-step that converts the protocol from something people are asked to follow into something the build requires.

## 2. Graph state (protocol step 2)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `e0062c2` |
| Graph indexed commit | `e0062c2` |
| **Match?** | **Yes** — verified before starting |
| Coverage | documentation only |
| Status | **`BLOCKED` for application code — static fallback** |

## 3. Target nodes
`.github/workflows/` (new), `tests/guards/change-impact-record.sh` (new), `INDEXING_AND_REFRESH` §2.

## 4. Dependencies
**Inbound:** none — CI is a leaf.
**Outbound:** the gate reads `docs/product/10-logs/blast-radius/` and sub-step front-matter. If those conventions change, the gate must change with them.

## 5. Impact by category
| Category | Affected | Confidence |
| --- | --- | --- |
| CI / delivery | **New** — verify, knowledge-graph and change-impact workflows | High |
| Tests | New `change-impact-record.sh` guard | High |
| Documentation | `INDEXING_AND_REFRESH` command reference; STEP-001.06 record | High |
| Code / contracts / data | **None** | High |
| **Process** | A merge can now be **blocked by machine**, not only by convention | High |

## 6. Design decision — the gate is a local script that CI invokes
GitHub Actions cannot be executed locally, so a gate written only as workflow YAML would be **unverifiable until a PR runs** — and an unverified gate is exactly the false assurance pattern that produced `BUG-004`.

The enforcement logic therefore lives in `tests/guards/change-impact-record.sh`, runnable and meta-testable **now**. The workflow is a thin caller.

Consequence: the *logic* is proven today; the *wiring* is not provable until a real PR exercises it. Recorded honestly below rather than claimed.

## 7. Risk
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | A too-strict gate blocks legitimate merges (e.g. docs-only changes) |
| Severity | 3 | A gate that blocks everything gets disabled — and a disabled gate is worse than none |
| Reach | 2 | Every future change passes through it |
| Detectability | 1 | Failures are loud and immediate |
| Reversibility | 1 | Workflow revert |
| **Confidence** | 3 | Logic meta-testable locally; **CI wiring unverifiable until a PR runs** |
| Customer criticality | 1 | No customer surface |

**Overall: MEDIUM** — raised from LOW deliberately. This is the first change whose failure mode is *process erosion* rather than a broken build, and confidence is capped by the unverifiable CI half.

## 8. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| Workflow actually runs on GitHub | Cannot execute Actions locally | **Open** — first PR is the real test |
| Exemption scope | Docs-only and chore commits must not be blocked, or the gate gets disabled | Mitigated by an explicit, tested exemption list |
| Runner has Node 24 + pnpm | Not yet observed on a runner | Pinned in the workflow; first run confirms |

## 9. Required actions
Write the gate script and meta-test it; write three workflows; document the command reference; state plainly that CI wiring is unproven until a PR runs.

## 10. Approval
Owner instructed to proceed. MEDIUM risk with a single owner — self-approved, which is the `ADR-010` four-eyes gap in practice. Noted, not hidden.

## 11. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | *(pending)* |
| `detect_changes()` | *(pending)* |
| Regression R1–R7 | *(pending)* |
| Gate meta-test | *(pending)* |

## 12. Disposition
*(pending)*
