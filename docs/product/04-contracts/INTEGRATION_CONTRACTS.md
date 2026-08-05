# JourneyLab — Integration Contracts

| Field | Value |
| --- | --- |
| Owner | Data Architect + Partnerships (unassigned — `BLK-001`) |
| Status | **All `PROPOSED`; no provider selected.** 10 of 11 external dependencies unidentified |
| Upstream source | Blueprint §9 (connector framework), §11 (webhooks) |
| Last reviewed | 2026-08-05 |

Navigation: [Integration architecture](../03-architecture/INTEGRATION_ARCHITECTURE.md) · [Data contracts](DATA_CONTRACTS.md) · [Dependencies](../02-delivery/DEPENDENCY_REGISTER.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Contract template — required for every provider

A provider may not be integrated until every field is filled. This is the acceptance checklist for `STEP-005`.

| Field | Requirement |
| --- | --- |
| Provider identity and contract owner | Named person, not a team alias |
| **Licence terms** | Permitted use, **cache duration**, attribution, redistribution limits, deletion obligations |
| Authentication | Mechanism, credential storage, rotation period |
| Endpoints consumed | Exact operations and their purpose |
| Request/response schema | Registered contract version |
| Rate limits and quota | Per environment, with headroom |
| Freshness SLA | Provider's commitment vs. our field-class requirement |
| Error taxonomy | Provider errors mapped to our internal classes |
| Circuit-breaker policy | Threshold, open duration, half-open probe |
| Checkpoint/cursor semantics | How resumption works |
| Backfill procedure | Bounded, idempotent, resumable |
| Reconciliation method | How we prove ingestion completeness |
| Sanitized fixtures | Success, empty, error, quota, schema-change cases |
| Sandbox availability | Whether integration tests can run without production calls |
| Deletion support | How provider-initiated deletion reaches our stores |
| Degradation behavior | Exactly what the user sees when this provider is down |
| Contract test | Consumer-driven contract test location |

---

## 2. Integration register

### INT-001 — Places, hours and accessibility *(`EXT-001`, critical path)*
| Field | Status |
| --- | --- |
| Provider | **Unidentified** — blocks `STEP-005`, drives `RISK-001` (exposure 20) |
| Consumed for | `Place` resolution, opening hours, closures, accessibility attributes, price ranges |
| Required freshness | Hours: fast class. Closures: minutes. Descriptions: slow class |
| Critical requirement | **Cache rights sufficient to keep evidence packs immutable** for scenario reproducibility (`ASM-019`, `ADR-004`) |
| Degradation | Circuit break → bounded cached data **explicitly marked stale** → block options requiring fresh hours |
| Failure to obtain | Triggers `RISK-001` stop condition — no viable alternative documented |
| Contract test | `tests/contracts/providers/places/` (`PROPOSED`) |

### INT-002 — Weather *(`EXT-002`)*
Forecast, alerts and historical normals. Must expose confidence or ensemble spread so `AI-007` can model uncertainty rather than invent it. Degradation: `weather_resilient` objective is withdrawn and the limitation disclosed — the scenario set shrinks rather than silently losing meaning.

### INT-003 — Transit *(`EXT-003`)*
Routes, schedules, service alerts, time-zone normalization. Feed version pinned. Degradation: walking/driving profiles only, with the transit gap disclosed. Alert latency is a Phase 3 freshness SLO.

### INT-004 — Routing and travel matrices *(`EXT-004`, `DEC-008`)*
| Field | Detail |
| --- | --- |
| Required profiles | walking, transit, driving, **wheelchair where data permits** |
| Contract requirement | The provider must **declare profile support explicitly**; silent fallback from wheelchair to walking is prohibited — it would make an accessibility claim we cannot support (`ASM-020`) |
| Caching | Matrices cached by mode × time window × **provider terms**; the terms are part of the cache key so licence-limited data cannot be over-retained |
| Degradation | Cached matrix marked stale; if absent, affected options blocked. **Straight-line distance is never substituted** |

### INT-005 — Affiliate deep link and attribution *(`EXT-005`)*
| Field | Detail |
| --- | --- |
| Outbound | Deep link carrying dates, party size, product identifiers where permitted (`ASM-012`) |
| Inbound | **Signed** webhook with event ID and creation time |
| Webhook rules | Verify signature **before parsing**; enforce replay window; accept duplicates idempotently; enqueue rather than process inline |
| Prohibited | Any payment credential in either direction (`REQ-BOOK-002`) |
| Reconciliation | Partner statement vs. recorded handoffs |
| Degradation | Copyable booking details (`REQ-BOOK-004`); `KPI-006` becomes unmeasurable and is reported as such |

### INT-006 — LLM provider *(`EXT-006`)*
| Field | Detail |
| --- | --- |
| Access | **Only** via the model gateway; no provider SDK in domain code |
| Contract | Structured JSON Schema output; per-request cost and latency budget; timeout |
| Data policy | **Provider training on our data must be contractually disabled**; residency and retention documented |
| Sent data | Prompts with redacted sensitive fields and retrieved evidence; never raw personal identifiers |
| Degradation | Failover provider → non-AI fallback (structured form, templated explanations) |

### INT-007 — Identity provider *(`EXT-007`, `DEC-004`)*
OIDC with passkey support. Token lifetime, refresh and revocation documented. Degradation: **fail closed** — authentication unavailability must never produce an anonymous authorized session.

### INT-008 — Map tiles *(`EXT-009`)*
Browser-side tile fetch. **No trip content in tile requests.** CSP allowlists exactly this origin. Degradation: list-only comparison, which `REQ-A11Y-003` already requires to be fully functional.

### INT-009 — Crowd signals *(privacy-gated)*
| Field | Detail |
| --- | --- |
| Hard requirement | **Aggregate occupancy only.** Individual-level or device-level data is rejected outright (`ASM-021`, `CON-003`) |
| Privacy review | Required before integration, not after |
| Degradation | The "quieter locations" preference is withdrawn and disclosed |

---

## 3. Universal integration rules

1. Every provider is reached through a **provider-independent interface** so substitution does not ripple into domain logic.
2. Every connector implements all eleven framework capabilities ([INTEGRATION_ARCHITECTURE](../03-architecture/INTEGRATION_ARCHITECTURE.md) §1) — partial implementation is not integration.
3. **Schema drift is rejected and alerted**, never coerced.
4. Provider identities are never exposed in public API responses or client-visible errors.
5. Every provider has documented, user-visible degradation behavior. "It just fails" is not acceptable.
6. Consumer-driven contract tests replay sanitized payloads before every release.
7. Provider concentration is reviewed before coverage expansion (`RISK-008`).

---

## 4. Outbound webhooks (JourneyLab as producer)

Not in Phase 1 scope. When introduced (advisor/partner integrations, Phase 4), they must: be signed, carry event ID and creation time, support replay, require idempotent receivers, and publish rate limits, freshness guarantees, pagination semantics, error codes and support policy in a developer portal.

---

## 5. Status summary

| Integration | Provider selected | Contract signed | Fixtures | Tests |
| --- | --- | --- | --- | --- |
| INT-001 … INT-004, INT-009 | ❌ | ❌ | ❌ | ❌ |
| INT-005 | ❌ | ❌ | ❌ | ❌ |
| INT-006, INT-007, INT-008 | ❌ | — | ❌ | ❌ |

**No integration exists.** This is the largest concentration of unresolved external dependency in the programme and the reason `STEP-005` is `BLOCKED` in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).
</content>
