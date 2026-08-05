# JourneyLab — Security Testing

| Field | Value |
| --- | --- |
| Owner | Security Architect (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — no tests, no scans, no pen test |
| Upstream source | Blueprint §16 (security testing), §14 (controls) |
| Last reviewed | 2026-08-05 |

Navigation: [Security architecture](../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) · [Authorization matrix](../04-contracts/AUTHORIZATION_MATRIX.md) · [Test strategy](TEST_STRATEGY.md) · [Incident response](../07-operations/INCIDENT_RESPONSE.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Continuous checks

| Check | Runs | Blocks | Owner |
| --- | --- | --- | --- |
| SAST | Every commit | Merge on high severity | Security |
| Dependency scanning | Every commit + daily | Merge on known-exploitable | Security |
| Container scanning | Every build | Deploy on high severity | SRE |
| IaC scanning | Every infra change | Merge on policy violation | SRE |
| Secret detection | Every commit + history scan | **Merge always** | Security |
| **Tenant isolation (R7)** | **Every sub-step** | Commit | Backend |
| Authorization matrix tests | Every commit | Merge | Backend |
| DAST | Nightly on staging | Release | Security |
| Authorization fuzzing | Nightly | Release | Security |
| Penetration test | Annual + before GA | GA | External |

---

## 2. Test categories

### Tenant isolation — `TST-SEC-002`
The highest-priority security test, run at every sub-step because a regression here is catastrophic and silent.

| Vector | Test |
| --- | --- |
| API | Tenant A token requesting tenant B resources → denied, identical response to not-found |
| Cache | Cache key collision cannot serve cross-tenant data |
| Background job | Job for tenant A cannot read or write tenant B rows |
| Export | Export contains only the requesting tenant's data |
| **Graph traversal** | Domain-graph query cannot traverse into another tenant, including via counts, path lengths or timing |
| Event consumption | Consumer cannot process another tenant's event into shared state |
| Vector search | Similarity search cannot return another tenant's chunks |
| Support diagnostics | Cannot be widened beyond one trip |

### Authorization — `TST-SEC-004`
Generated from [AUTHORIZATION_MATRIX](../04-contracts/AUTHORIZATION_MATRIX.md), so a matrix change without a test change fails CI. Every cell is tested, not sampled. Includes: owner-only operations (canonical selection, repair acceptance), four-eyes (a curator cannot self-approve), collaborator limits, guest limits, curator PII isolation.

### Injection and untrusted content — `TST-SEC-006`, `TST-AI-009`
| Vector | Test |
| --- | --- |
| Prompt injection via provider content | Embedded instructions do not alter behavior or trigger tools |
| Injection via MCP tool descriptions | Tool metadata treated as untrusted |
| SQL/NoSQL injection | Parameterised queries verified |
| XSS via evidence text | Provider and model content rendered inert |
| SSRF via provider payload URLs | Egress allowlist blocks; no internal metadata endpoints reachable |
| Path traversal in exports/offline packs | Rejected |

### Data protection
| Test | Pass condition |
| --- | --- |
| Encryption in transit and at rest | Verified per store |
| Redaction | No secrets or PII in logs, traces, graph properties or embeddings |
| **Deletion proof — `TST-PRIV-006`** | Seeded data in every store absent after deletion |
| Booking-document segregation | Planning-graph credentials cannot read booking documents |
| Backup encryption | Verified; restore does not leak across tenants |

### Supply chain
SBOM generated; artifacts signed and verified at deploy; unsigned artifacts rejected; lock files enforced; protected branches and reviewed deployments verified.

---

## 3. Abuse-case testing

Security testing that is specific to this product's harms, not generic OWASP coverage:

| Abuse case | Test |
| --- | --- |
| **Stalking via shared itinerary** | Revoked link fails closed immediately; view log records access; forwarded link cannot outlive expiry |
| Location inference | No API or export reveals precise location when sharing is off |
| Sensitive-constraint disclosure | A collaborator cannot read another's accessibility constraint via any endpoint, graph query or export |
| Enumeration | Trip and user IDs are not enumerable; 403 and 404 are indistinguishable |
| Data poisoning | A malicious provider fact cannot silently change a canonical plan without curator review |
| Model misuse | The model cannot be induced to authorise, book or mutate state |
| Scraping | Rate limits and quotas prevent bulk extraction of licensed destination data |

---

## 4. Findings management

| Severity | Response | Release impact |
| --- | --- | --- |
| **Critical** — cross-tenant exposure, auth bypass, secret leak | Immediate SEV1, halt release | Blocks |
| High | Fix before next release | Blocks |
| Medium | Scheduled with an owner and date | Documented exception only |
| Low | Backlog | None |

Every finding gets a regression test (R6), so a fixed vulnerability cannot silently return.

---

## 5. Status

| Item | Status |
| --- | --- |
| `tests/security/` | Does not exist |
| CI security scanning | Not configured |
| Threat model | Not produced (`STEP-023`) |
| Penetration test | Not scheduled |
| Isolation tests | **Cannot run — no application** |

**Precondition for GA:** threat model closed or accepted, pen test complete, all critical/high findings resolved, deletion proof passing.
