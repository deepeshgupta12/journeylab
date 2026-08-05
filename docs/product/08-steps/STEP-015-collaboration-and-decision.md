---
step_id: STEP-015
title: Collaboration and decision
status: DEFERRED
release: Phase 2
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-013, STEP-002]
requirement_ids: [REQ-COLL-001, REQ-COLL-002, REQ-COLL-003, REQ-COLL-004, REQ-TRIP-006, REQ-SEC-008]
api_ids: [API-010, API-008]
event_ids: [EVT-004]
data_ids: [DATA-004, DATA-003]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-015 — Collaboration and decision

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 2.**

## 1. Outcome
A group contributes constraints, votes and proposals; conflicting hard constraints are visible **without exposing anyone's sensitive details**; the owner approves the final selection and can reconstruct who proposed, approved and changed every material choice.

## 2. Why this step exists
Blueprint consequence `CQ-004`: groups cannot see whose constraint caused a conflict or what trade-off restores feasibility. Solving that without turning the product into a surveillance tool for its own users is the design challenge.

## 3. Scope
Secure-link and account invitations with expiry and revocation; scoped view/comment/propose permissions; conflict attribution without sensitive disclosure; votes and immutable change proposals; owner approval for final selection; full audit trail.

## 4. Explicit exclusions
Advisor delegated access is [STEP-028](STEP-028-advisor-workspace-and-commercial-scale.md). Edit mechanics are [STEP-014](STEP-014-interactive-what-if-editing.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 owner | Full; **sole authority to select canonical** | Whole trip | PII |
| PER-002 collaborator | Invitation-scoped view/comment/propose | Scoped trip; own constraints | **Sensitive** |

## 6. Preconditions and dependencies
[STEP-013](STEP-013-visual-comparison.md), [STEP-002](STEP-002-identity-tenancy-and-authorization.md); anti-abuse controls implemented.

## 7. Inputs and source systems
Invitation permissions, collaborator constraints, comments, votes, proposed changes.

## 8. Detailed normal workflow
1. Owner invites by secure link or account with a chosen scope and expiry.
2. Collaborator accepts and adds their own hard and soft constraints.
3. Solver treats collaborator hard constraints as first-class.
4. Where constraints conflict, the system attributes the conflict **by person and class, not by value**.
5. Collaborators vote, comment and propose changes as immutable proposals.
6. Owner reviews and approves; `API-008` sets the canonical scenario and emits `EVT-004`.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Link expired or revoked | **Fail closed, leak nothing** | Generic access-denied | REQ-SEC-008 |
| Conflicting hard constraints | Show minimal conflict set with attribution by class | Group can negotiate | REQ-COLL-002 |
| Collaborator attempts canonical selection | Denied | Owner-only enforced | REQ-COLL-001 |
| Concurrent proposals | Both preserved; owner arbitrates | No silent loss | REQ-COLL-004 |
| Collaborator deletes their data | Contributions removed/pseudonymised; **owner's trip survives** | Trip intact | REQ-PRIV-006 |

## 10. State machine and lifecycle transitions
Invitation: `issued → accepted → active → (expired | revoked)`. Proposal: `open → (accepted | rejected | superseded)`. Immutable throughout.

## 11. Frontend implementation
`apps/web/src/features/collaboration/` (`PROPOSED`) — invitation manager, proposal list, vote panel, conflict attribution view. Conflicts communicated in text, not colour alone.

## 12. Backend implementation
`services/collaboration/src/proposals.py` (`PROPOSED`) — optimistic concurrency, immutable change proposals, audit trail.

## 13. API, event and integration contracts
`API-010` invitations with scoped, expiring permissions; `API-008` selection (owner only). `EVT-004` carries the decision context.

## 14. Data model, migration and retention effects
Extends `DATA-004` with membership and invitation records; references `DATA-003` collaborator constraints. Invitations carry expiry; view logs carry their own retention.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: conflict attribution and voting are deterministic. Using a model to summarise a group's disagreement would risk paraphrasing a sensitive constraint into visibility — the precise harm `REQ-COLL-002` prevents.

## 16. Security, privacy, accessibility and responsible-AI controls
**`SC-ABUSE-01` is the defining control here:** expiring invitations, view logs, download controls, location sharing default off — `RISK-006` (stalking) is a real harm in shared travel plans. Sensitive constraints are solver-visible but never rendered verbatim to others. Invitation flows are completable without the map.

## 17. Observability, analytics and KPIs
`invite_sent`, `vote_cast`, proposal acceptance rate, time-to-group-decision, revocation frequency, expired-link access attempts (an abuse signal).

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014 mandatory** (sensitive-constraint exposure paths) |
| Expected impact | Touches authorization and sensitive data — high scrutiny |

## 20. Blast-radius assessment
High privacy severity. A defect here exposes one person's accessibility or budget constraint to a group — irreversible once seen. Every sub-step requires the data-flow check and owner approval.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-015.01 | Invitation issue, scope, expiry, revocation |
| STEP-015.02 | Collaborator constraint contribution |
| STEP-015.03 | Conflict attribution **by class, never by value** |
| STEP-015.04 | Comments and votes |
| STEP-015.05 | Immutable change proposals with optimistic concurrency |
| STEP-015.06 | Owner approval and canonical selection |
| STEP-015.07 | Audit trail and view logs |
| STEP-015.08 | Anti-abuse controls and fail-closed access |

## 22. Test and evaluation plan
`TST-COLL-001` … `TST-COLL-004`, `TST-TRIP-006`, `TST-SEC-008`. A dedicated abuse test: a revoked link must fail immediately and a forwarded link must not outlive expiry.

## 23. Deployment, feature flag and migration plan
Behind a Phase 2 flag. Invitation expiry defaults are conservative and configurable downward only.

## 24. Rollback, compensation and recovery plan
Flag off disables new invitations; existing collaborators lose access cleanly. **An exposure cannot be rolled back** — which is why the controls are preventive rather than detective.

## 25. Acceptance criteria
- [ ] Collaborators cannot select canonical or alter protected bookings (`REQ-COLL-001`)
- [ ] Sensitive constraints are solver-usable but never displayed verbatim to others (`REQ-COLL-002`)
- [ ] Final selection requires explicit owner approval (`REQ-COLL-003`)
- [ ] Owner can reconstruct who proposed, approved and changed every material choice (`REQ-COLL-004`)
- [ ] Invitations are role-scoped, expiring and revocable (`REQ-TRIP-006`)
- [ ] Sharing defaults to no location; views are logged (`REQ-SEC-008`)

## 26. Evidence required for completion
Sensitive-disclosure test results; revocation timing test; audit-trail reconstruction demonstration; abuse-case test report.

## 27. Open questions, risks and decisions
`RISK-006` stalking risk. How much conflict detail is useful without being disclosing is a genuine design tension requiring user research, not a coding decision.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
