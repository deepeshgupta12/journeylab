# JourneyLab — Authorization Matrix

| Field | Value |
| --- | --- |
| Owner | Security Architect (unassigned — `BLK-001`) |
| Status | `PROPOSED` — authoritative specification; no enforcement code exists |
| Upstream source | Blueprint §5 (personas), §14 (security), §11 (per-operation auth) |
| Last reviewed | 2026-08-05 |

Navigation: [Personas](../01-product/PERSONAS_AND_JOBS.md) · [API contracts](API_CONTRACTS.md) · [Security](../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Enforcement model

Authorization is decided by three independent checks, **all of which must pass**:

1. **Tenant scope** — does the actor belong to the organization owning the resource? Enforced by row-level security at the database, so an application bug cannot bypass it.
2. **Role capability** — does the actor's role permit this operation class?
3. **Resource relationship** — is the actor the owner, an invited member with the right scope, or a delegated operator?

**Client-side role checks are presentation only** (`REQ-SEC-004`). The server is the control.

---

## 2. Roles

| Role | Assigned to | Scope |
| --- | --- | --- |
| `guest` | Unauthenticated session with a claimed trip | Single trip, no sharing, no export of others' data |
| `trip_owner` | Trip creator (PER-001) | Full control of own trip |
| `trip_editor` | Invited collaborator with edit scope (PER-002) | Propose and edit non-protected elements |
| `trip_viewer` | Invited collaborator, read/comment (PER-002) | Read + comment + vote |
| `advisor` | Organization member (PER-003, Phase 4) | Delegated trip access within the org, audited |
| `curator` | Internal (PER-004) | Destination facts only — **no traveler PII** |
| `ops_admin` | Internal (PER-005) | Providers, flags, incidents, support diagnostics — **no raw PII by default** |
| `privacy_operator` | Internal | Executes DSRs, audited |
| `service` | Workload identity | Narrow, per-service capability |

---

## 3. Operation matrix

`✅` permitted · `❌` denied · `⚠️` permitted with conditions · `📋` audited

| Operation | API | guest | trip_owner | trip_editor | trip_viewer | advisor | curator | ops_admin | privacy_operator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Create trip | API-001 | ✅ own | ✅ | ❌ | ❌ | ⚠️📋 delegated | ❌ | ❌ | ❌ |
| Read trip | API-002 | ✅ own | ✅ | ✅ | ✅ | ⚠️📋 | ❌ | ❌ | ⚠️📋 DSR only |
| Replace brief | API-003 | ✅ own | ✅ | ✅ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| Build evidence pack | API-004 | ✅ own | ✅ | ✅ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| Generate scenarios | API-005 | ✅ own | ✅ | ✅ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| List/read scenarios | API-006/007 | ✅ own | ✅ | ✅ | ✅ | ⚠️📋 | ❌ | ❌ | ❌ |
| **Select canonical scenario** | API-008 | ✅ own | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create what-if edit | API-009 | ✅ own | ✅ | ✅ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| Modify protected item | API-009 | ⚠️ explicit unlock | ⚠️ explicit unlock | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Invite collaborator | API-010 | ❌ | ✅ | ❌ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| Booking handoff | API-011 | ✅ own | ✅ | ✅ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| Activate live trip | API-012 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Generate repairs | API-013 | ❌ | ✅ | ✅ | ❌ | ⚠️📋 | ❌ | ❌ | ❌ |
| **Accept repair** | API-013 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit feedback | API-014 | ✅ own | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Export / delete own data | API-015 | ✅ own | ✅ | ✅ own | ✅ own | ✅ own | ❌ | ❌ | ✅📋 |
| Override destination fact | API-016 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅📋 | ❌ | ❌ |
| **Approve high-impact override** | API-016 | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ **second curator** | ⚠️📋 | ❌ |
| Read coverage | API-017 | ✅ public | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Disable provider / roll back model | — | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅📋 | ❌ |
| Read support diagnostic bundle | — | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️📋 single trip, no raw PII | ⚠️📋 |
| Query knowledge graph | API-018 | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ facts subgraph | ⚠️📋 code graph | ❌ |

---

## 4. Conditional rules

| Rule | Detail |
| --- | --- |
| **Owner-only decisions** | Canonical scenario selection and repair acceptance can never be delegated to a collaborator or performed automatically (`REQ-COLL-003`, `REQ-LIVE-005`) |
| **Four-eyes** | A high-impact fact override requires a second curator; **the actor may never be their own approver** (`REQ-ADMIN-002`) |
| **Collaborator constraint privacy** | A collaborator's sensitive constraint is usable by the solver but not displayed verbatim to others (`REQ-COLL-002`) |
| **Support scoping** | Diagnostics reconstruct exactly one trip; there is no operation that grants unrestricted tenant access (`REQ-ADMIN-005`) |
| **Curator isolation** | Curators see destination facts only; no operation exposes traveler PII to a curator |
| **Guest limits** | A guest may plan and export their own trip but may not invite collaborators or activate a live trip |
| **Advisor delegation** | Requires an explicit delegation record; every access is audited; an advisor may not silently edit a client-approved canonical plan (`REQ-TRIP-009`) |
| **Graph traversal** | A graph answer must never reveal a path the caller cannot inspect at its source (`REQ-KG-006`) |
| **Service identity** | Workload identity with the narrowest capability; no service holds a blanket admin role |

---

## 5. Denial behavior

| Situation | Response |
| --- | --- |
| Not permitted | `403` — **identical shape to `404`** so resource existence is not disclosed |
| Unknown resource | `404` with the same body shape |
| Expired/revoked invitation | `403 collaboration.invitation_expired`, leaking no trip content |
| Cross-tenant attempt | Denied, audited, and **SEV1 alert** (`ALRT-SEC-001`) |
| Missing tenant context | Request rejected at the boundary — never defaults to "any tenant" |

---

## 6. Testing obligations

| Test | Coverage |
| --- | --- |
| TST-SEC-002 | Cross-tenant read/write/cache/job/export/graph isolation |
| TST-SEC-004 | Every operation denies unauthorized roles; matrix-driven, not sampled |
| TST-ADMIN-002 | Four-eyes cannot be satisfied by the same actor twice |
| TST-COLL-001/002 | Collaborator cannot select canonical or read others' sensitive constraints |
| TST-ADMIN-005 | Support path cannot be widened to multi-trip access |
| TST-KG-006 | Graph traversal respects repository, tenant and source permissions |

**This matrix is the test fixture.** Authorization tests are generated from it so a matrix change without a test change fails CI.
</content>
