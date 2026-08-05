# JourneyLab — Release Readiness Checklist

| Field | Value |
| --- | --- |
| Owner | TPM (unassigned — `BLK-001`) |
| Status | `READY` — checklist binding for every release |
| Current release readiness | **NOT READY** — see §11 |
| Last reviewed | 2026-08-05 |

Navigation: [Release plan](../02-delivery/RELEASE_PLAN.md) · [Test strategy](TEST_STRATEGY.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md) · [Definition of done](../01-product/OUT_OF_SCOPE.md#5-definition-of-done-for-general-availability) · [00-START-HERE](../00-START-HERE.md)

---

## How to use

Every box needs **evidence**, not an opinion — a test run, a report, a drill record, a signature. An unchecked box blocks the release; it does not become a follow-up item.

---

## 1. Product acceptance
- [ ] Every step in the release is `VERIFIED` in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md)
- [ ] Every step's acceptance criteria met with recorded evidence (step file §25, §26)
- [ ] Every requirement in scope has a passing acceptance test
- [ ] Deferred scope is explicitly gated, not silently missing
- [ ] Open decisions blocking this release are closed

## 2. Contract compatibility
- [ ] OpenAPI/AsyncAPI diff reviewed; breaking changes carry version, migration guide, notice, dual-run window, sunset date
- [ ] Generated clients regenerated and committed; no hand edits
- [ ] Consumer-driven contract tests pass
- [ ] Deprecated operations have sunset dates and no active consumers past sunset

## 3. Database and event migration
- [ ] Expand/migrate/contract plan documented
- [ ] Backward compatible through the full rollout window
- [ ] Migration rehearsed on production-like data with timing recorded
- [ ] Rollback rehearsed; no rollback path loses data
- [ ] Event schema changes classified and dual-published if breaking

## 4. Security
- [ ] Threat-model actions closed or explicitly accepted with an owner
- [ ] SAST, DAST, dependency, container, IaC scans clean of critical/high
- [ ] Secret detection clean, including history
- [ ] **Tenant isolation tests pass** (`TST-SEC-002`)
- [ ] Authorization matrix tests pass for every cell
- [ ] Penetration test complete (GA); findings resolved
- [ ] SBOM generated; artifacts signed; unsigned artifacts cannot deploy

## 5. Privacy
- [ ] Data inventory current for every source
- [ ] Consent flows tested, including independent withdrawal
- [ ] **Deletion proof passes across primary, object, vector, graph, cache, export and token stores** (`TST-PRIV-006`)
- [ ] Export produces machine-readable data with confirmation
- [ ] Deletion failure retry queue monitored and visible to the privacy owner
- [ ] No sensitive class used for advertising or unrelated personalization

## 6. Accessibility
- [ ] WCAG 2.2 AA audit passed
- [ ] **Map-free keyboard and screen-reader journey completes all MVP tasks**
- [ ] Every visualization has a table/list equivalent and CSV export
- [ ] Non-colour status indicators verified
- [ ] Reduced motion, high contrast and 200% zoom verified

## 7. Observability and support
- [ ] Dashboards live for API, provider, evidence freshness, solver, AI quality/cost, queues, privacy, KG
- [ ] Every alert has a runbook and a named owner
- [ ] Business-quality alerts verified with synthetic probes (citation failure, hard-constraint regression, stale coverage)
- [ ] End-to-end trip correlation trace works
- [ ] Tenant-safe support diagnostic bundle tested
- [ ] On-call rotation defined; escalation path published

## 8. Cost and capacity
- [ ] Cost per saved feasible trip measured against budget (`KPI-007`)
- [ ] Provider quota headroom confirmed
- [ ] Solver pool sized against measured generation demand
- [ ] Cost alerts configured

## 9. Model and data
- [ ] AI evaluation gates pass on gold **and** adversarial sets
- [ ] **Zero hard-constraint violations** in the full release corpus
- [ ] **Citation correctness ≥ 95%** on volatile facts
- [ ] Abstention behavior verified on sparse evidence
- [ ] Cost/latency budgets enforced and measured
- [ ] Model rollback proven independent of application deploy
- [ ] Non-AI fallback verified working for every AI capability
- [ ] Data-quality expectations pass; reconciliation clean
- [ ] Destination pack coverage, freshness and licence current

## 10. Knowledge graph and change control
- [ ] Graph indexed **at the release commit**
- [ ] **Immutable release graph tagged** (`REQ-KG-004`)
- [ ] Coverage ≥ 95% of first-party files; ≥ 90% of public symbols owned
- [ ] Extraction gaps reviewed, not merely reported
- [ ] Edge precision measured (required before impact results gate a release)
- [ ] **Every change in the release has a completed blast-radius record** with post-change evidence
- [ ] No unowned API, event, migration, model or production service
- [ ] Untested-requirement and orphan-node counts did not increase

## 11. Resilience and recovery
- [ ] Provider outage and stale-data drills demonstrate safe degradation without fabricated facts
- [ ] Solver timeout preserves the last valid version
- [ ] Backup restoration exercised within the quarter
- [ ] DR playbook rehearsed
- [ ] Canary abort conditions configured and tested
- [ ] Automated rollback exercised in staging

## 12. Documentation
- [ ] All documentation current at the release commit
- [ ] Runbooks, model cards, data contracts and API clients current
- [ ] [CHANGELOG](../02-delivery/CHANGELOG.md) updated with compatibility classifications
- [ ] Logs current: implementation, bug, enhancement, regression
- [ ] Release notes contain **no AI co-authorship attribution** (`ADR-006`)

---

## Sign-off

| Role | Name | Date | Signature |
| --- | --- | --- | --- |
| Product Lead | | | |
| Product Architect | | | |
| Security Architect | | | |
| Privacy Owner | | | |
| Data Architect | | | |
| AI/ML Architect | | | |
| Frontend Lead | | | |
| SRE | | | |
| TPM | | | |

**No release proceeds without every signature.** Nine unassigned roles is itself the current blocker.

---

## Current readiness assessment

**NOT READY.** Not a single section can be evaluated:

| Blocker | Detail |
| --- | --- |
| `BLK-001` | No named owners — no sign-off is possible |
| `BLK-002` | No application code, tests, contracts, pipelines or infrastructure |
| `DEC-002` | No destination region — no evaluation corpus can exist |
| `DEC-005` | No KPI thresholds — gates are not objectively evaluable |
| `DEC-007` | No deployment target |
| `RISK-001` | Provider licence viability unproven |
| `RISK-014` | Knowledge graph covers documentation only |

The honest status is **pre-implementation**: the documentation system that defines this release exists; the release does not.
</content>
