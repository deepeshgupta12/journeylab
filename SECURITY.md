# Security Policy

**Owner:** Deepesh Kumar Gupta (`@deepeshgupta12`) — see [ADR-010](docs/product/02-delivery/DECISION_LOG.md).

## Reporting a vulnerability

Report privately via GitHub Security Advisories on this repository. **Do not open a
public issue.** Include reproduction steps, affected paths and observed impact.

Acknowledgement target: within a reasonable working period. Formal SLAs are not yet
defined — this is a pre-release repository with no production deployment.

## Scope

JourneyLab is **pre-implementation**: no application code is deployed and no user
data exists. Reports about the documentation system, build tooling or supply chain
are in scope.

## Severity and response

Severity follows [BUG_REGISTER](docs/product/10-logs/BUG_REGISTER.md):

| Level | Examples | Response |
| --- | --- | --- |
| **S1** | Cross-tenant exposure, data loss, privacy breach, a delivered plan violating a hard constraint | Stop the line; incident response; release halted |
| **S2** | Core journey broken; citation correctness below gate; stale provider data presented as current | Fix before the next sub-step proceeds |
| **S3** | Defect with a workaround; repository hygiene | Scheduled within the step |
| **S4** | Cosmetic | Backlog |

Every fixed security defect gains a regression test (check **R6**), so it cannot
silently return.

## Controls in force

Full register in
[SECURITY_PRIVACY_RESPONSIBLE_AI](docs/product/03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md).
Notable pre-implementation controls:

- Secret scanning from the first commit
- No dependency or build artifacts tracked in git (guard: `tests/guards/no-tracked-artifacts.sh`)
- Lock files pinned; dependency changes reviewed
- **No AI co-authorship attribution in commits** ([ADR-006](docs/product/02-delivery/DECISION_LOG.md))

## Known accepted gap

**Four-eyes approval (`REQ-ADMIN-002`, `SC-GOV-02`) is structurally unsatisfiable**
with a single owner. Recorded in ADR-010; must be resolved before `STEP-021` ships.
