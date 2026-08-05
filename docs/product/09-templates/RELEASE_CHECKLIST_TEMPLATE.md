# Release Checklist — Template

> Per-release instance of [RELEASE_READINESS_CHECKLIST](../06-quality/RELEASE_READINESS_CHECKLIST.md).
> Copy to `10-logs/releases/REL-<version>-checklist.md`.
> **Every box needs evidence — a test run, a report, a drill record, a signature. Not an opinion.**

---

```markdown
# Release [version] — Readiness Checklist

| Field | Value |
| --- | --- |
| Release | |
| Type | patch / minor / major / model / data / destination-pack |
| Target date | |
| Release manager | |
| Commit | |
| Steps included | STEP-… |
| Sub-steps included | STEP-NNN.MM … |

## 1. Scope confirmation
- [ ] All included steps `VERIFIED` in the tracker
- [ ] No step `IN_PROGRESS` or `BLOCKED` in this release
- [ ] Deferred scope explicitly gated, not silently missing
- [ ] Blocking decisions closed

## 2. Product acceptance
- [ ] Acceptance criteria met with evidence (step §25, §26)
- [ ] Requirements in scope have passing tests

## 3. Contracts
- [ ] Compatibility diff reviewed · Evidence:
- [ ] Breaking changes carry version + migration guide + notice + dual-run + sunset
- [ ] Generated clients current, no hand edits
- [ ] Consumer contract tests pass

## 4. Data and migration
- [ ] Expand/migrate/contract plan documented
- [ ] Rehearsed on production-like data · Timing:
- [ ] Rollback rehearsed, no data loss
- [ ] Event schema changes classified

## 5. Security and privacy
- [ ] Scans clean of critical/high · Evidence:
- [ ] **Tenant isolation tests pass** (`TST-SEC-002`)
- [ ] Authorization matrix fully tested
- [ ] **Deletion proof across all stores** (`TST-PRIV-006`)
- [ ] Consent flows tested
- [ ] Threat-model actions closed or accepted

## 6. Accessibility
- [ ] WCAG 2.2 AA audit passed · Evidence:
- [ ] **Map-free keyboard + screen-reader journey completes all MVP tasks**
- [ ] Table/CSV equivalents present

## 7. Quality gates (product-specific)
- [ ] **Zero hard-constraint violations** in the release corpus
- [ ] **Citation correctness ≥ 95%**
- [ ] Scenario generation p95 ≤ 45 s
- [ ] Reproducibility verified (same inputs + seed)
- [ ] Abstention verified on sparse evidence
- [ ] Non-AI fallback verified for every AI capability

## 8. Observability and support
- [ ] Dashboards live · Alerts firing correctly (synthetic probe)
- [ ] Every alert has a runbook with an owner
- [ ] End-to-end trip trace works
- [ ] Support diagnostic bundle tested
- [ ] On-call briefed

## 9. Knowledge graph and change control
- [ ] Graph indexed **at the release commit** · Commit:
- [ ] **Immutable release graph tagged**
- [ ] Coverage ≥ 95% files, ≥ 90% symbols owned
- [ ] **Every change has a completed blast-radius record**
- [ ] Untested-requirement and orphan counts did not increase
- [ ] No unowned API, event, migration, model or service

## 10. Resilience
- [ ] Provider outage + stale-data drills pass — no fabricated facts
- [ ] Backup restoration exercised this quarter
- [ ] Canary abort conditions configured
- [ ] Automated rollback exercised in staging

## 11. Cost
- [ ] Cost per saved feasible trip measured vs. budget
- [ ] Provider quota headroom confirmed

## 12. Documentation and logs
- [ ] All docs current at the release commit
- [ ] [CHANGELOG](../02-delivery/CHANGELOG.md) updated with classifications
- [ ] Implementation, bug, enhancement and regression logs current
- [ ] Runbooks, model cards, data contracts current
- [ ] **Release notes contain no AI co-authorship attribution**

## 13. Rollout plan
| Field | Value |
| Strategy | blue/green / canary |
| Canary % and hold | |
| Abort conditions | |
| Rollback trigger and owner | |

## 14. Sign-off
| Role | Name | Date | Signature |
| Product Lead | | | |
| Product Architect | | | |
| Security Architect | | | |
| Privacy Owner | | | |
| Data Architect | | | |
| AI/ML Architect | | | |
| Frontend Lead | | | |
| SRE | | | |
| TPM | | | |

## 15. Post-release (24 h / 7 days)
- [ ] Trip trace verified in production
- [ ] Business-quality alerts verified
- [ ] Deletion propagation verified on a test account
- [ ] Pre/post graph neighborhoods compared
- [ ] Cost per trip reviewed
- [ ] Reported incorrect facts reviewed **separately** from satisfaction
- [ ] Negative results recorded in the decision log
```

---

**An unchecked box blocks the release.** It does not become a follow-up item — that is how gates decay into rituals.
