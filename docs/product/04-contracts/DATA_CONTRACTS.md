# JourneyLab — Data Contracts

| Field | Value |
| --- | --- |
| Owner | Data Architect (Deepesh Kumar Gupta) |
| Status | **All contracts `PROPOSED`** — no schema or migration exists |
| Upstream source | Blueprint §12 (data model and lifecycle), §9 (ingestion) |
| Last reviewed | 2026-08-05 |

Navigation: [Data architecture](../03-architecture/DATA_ARCHITECTURE.md) · [Event contracts](EVENT_CONTRACTS.md) · [Retention & deletion](../07-operations/DATA_RETENTION_AND_DELETION.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Internal dataset contracts

Each contract states owner, grain, keys, time semantics, quality expectations, classification, retention and breaking-change policy.

### DATA-004 — `Trip`
| Field | Value |
| --- | --- |
| Owner | `trip` module · **Grain** one row per journey |
| Keys | PK `trip_id`; FK `owner_user_id`, `organization_id`, nullable `canonical_scenario_version_id` |
| Time semantics | `created_at`, `updated_at` (system time); `start_date`/`end_date` are **local dates with an IANA time zone**, not timestamps |
| Quality | Date range within coverage bounds; exactly 0 or 1 canonical scenario |
| Classification | PII · **Consent** planning purpose |
| Retention | User-configurable within policy; default documented in retention policy |
| Deletion | Cascades to briefs, scenarios, items, feedback, packs (if unshared), graph nodes, vectors, caches, exports |
| Breaking change | Adding a required column requires expand/migrate/contract |

### DATA-005 — `TripBrief`
| Field | Value |
| --- | --- |
| Grain | One **immutable** row per confirmed brief version |
| Keys | PK `brief_id`; FK `trip_id`; unique (`trip_id`, `version`) |
| Structure | Four separate collections: `hard[]`, `soft[]`, `inferred[]`, `unresolved[]` — never a single typed-union list |
| Time semantics | `confirmed_at`; brief applies to the trip's local date range |
| Quality | Every entry has a unit and a priority; every `inferred` entry has a provenance reference |
| Classification | PII + **sensitive** (accessibility constraints) |
| Deletion | With the trip |
| Note | Immutability is what makes a scenario reproducible; an in-place edit would silently invalidate every scenario referencing it |

### DATA-007 — `EvidenceFact`
| Field | Value |
| --- | --- |
| Grain | One atomic claim about one subject |
| Keys | PK `fact_id`; FK `place_id`; index on (`subject`, `field`, `effective_from`) |
| Required fields | `value`, `unit`, `source_id`, `observed_at`, `effective_from`, `effective_to`, `confidence`, `access_label`, `licence_id` |
| Time semantics | **Three axes** — `observed_at`, effective window, `recorded_at` |
| Quality | Freshness per field class; conflicting facts retained, never merged |
| Classification | Licensed third-party data |
| Retention | Per provider licence (`SC-LIC-01`) |
| Deletion | Provider-initiated deletion propagates to packs, vectors and graph |
| Breaking change | Adding a field class requires a freshness policy entry first |

### DATA-008 — `EvidencePack`
Immutable collection + coverage report used by one generation run. **Cannot be mutated or deleted while a scenario references it.** Grain: one per generation. Classification: licensed. Note: this is the reproducibility anchor (`ADR-004`).

### DATA-010 / DATA-011 — `Scenario` / `ScenarioVersion`
| Field | Value |
| --- | --- |
| Grain | One scenario per objective per run; one version per edit |
| Required lineage | `brief_id`, `evidence_pack_id`, `solver_config_version`, `random_seed`, `model_versions[]` — **all four required at creation** |
| Invariant | Zero hard-constraint violations is a creation precondition |
| Structure | Immutable itinerary DAG with costs, score components, constraint results, change explanation |
| Classification | Derived, PII-adjacent (reveals travel plans) |
| Deletion | With the trip |

### DATA-013 — `BookingReference`
Segregated store, narrower access, shorter retention. **Payment credentials structurally excluded** — no column exists for them. Grain: one per confirmed external booking. Classification: **sensitive**. Deletion: with the trip or earlier.

### DATA-016 — `ConsentRecord`
One row per purpose per subject, with basis, timestamp and withdrawal. Withdrawing one purpose must not cascade to unrelated purposes. Retained after account deletion **only where legally required**, documented as an explicit exception.

*(DATA-001/002/003/006/009/012/014/015 follow the same contract shape; entity definitions are in [DATA_ARCHITECTURE](../03-architecture/DATA_ARCHITECTURE.md) §2.)*

---

## 2. External source contracts

One per provider. **No provider is selected**, so all fields are the required shape, not a described integration.

| Contract | Source | Grain | Time semantics | Quality expectations | Freshness | Reconciliation | Classification | Consent/purpose | Retention | Breaking-change policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DC-EXT-001 | Places / hours / accessibility (`EXT-001`) | One place record | Provider `updated_at` → `observed_at`; seasonal hours → effective window | Required: stable ID, coordinates, category. Hours must parse to intervals with a time zone | Hours: fast class. Descriptions: slow class | Record count + checksum vs. provider index | Licensed | Planning | Per licence | Schema drift ⇒ **reject and alert**, never coerce |
| DC-EXT-002 | Weather (`EXT-002`) | One forecast per location per period | Forecast issue time + valid period | Confidence or ensemble spread required for uncertainty modelling | Hours | Spot-check against reissued forecasts | Licensed | Planning | Short | Reject on drift |
| DC-EXT-003 | Transit (`EXT-003`) | Route/stop/schedule + alerts | Service dates; alert validity windows | Stop coordinates resolvable; service calendar complete | Alerts: minutes | Trip count vs. feed manifest | Licensed/open | Planning | Per licence | Feed version pinned |
| DC-EXT-004 | Routing matrices (`EXT-004`) | One matrix per mode × time window | Query time; validity per provider terms | Profile support declared explicitly (incl. wheelchair) | Cache per terms | Sampled re-query comparison | Licensed | Planning | **Cache key includes licence terms** | Profile removal is breaking |
| DC-EXT-005 | Affiliate attribution (`EXT-005`) | One callback per booking event | Event creation time | **Signature required**; replay window enforced | Real time | Partner statement vs. recorded handoffs | Commercial + PII-adjacent | Booking handoff | Per agreement | Signed schema version |
| DC-EXT-009 | Crowd signals (`EXT-009`) | Aggregated occupancy per place per period | Observation window | **Must be aggregate, never individual-level** (`ASM-021`) | Hours | Distribution sanity checks | Licensed, **privacy-gated** | Planning | Short | Rejected if individual-level |

---

## 3. Universal source rules

1. **No ingestion without a licence record** stating permitted use, cache duration and attribution (`REQ-DATA-001`).
2. **Schema drift is rejected, not coerced.** A provider changing a field's meaning is a breaking change requiring a contract update.
3. **Provenance is mandatory** — a fact without source, observed time and confidence cannot enter the canonical layer.
4. **Reconciliation is required.** Ingestion that cannot be reconciled against a source total is treated as incomplete.
5. **Deletion obligations propagate** to canonical entities, packs, vectors, graph and exports.
6. **Aggregate-only for behavioral signals.** Crowd data must never be individual-level.

---

## 4. Data-quality expectations

Expressed as executable expectations in `data/quality/domain_expectations.yml` (`PROPOSED`, created in `STEP-006`):

| Expectation | Rule | Failure |
| --- | --- | --- |
| Schema | Matches registered contract | Reject batch, alert |
| Freshness | Age-at-use within field class threshold | Mark stale; lower confidence; block if critical |
| Completeness | Planning-critical fields present | Exclude from candidates with a stated reason |
| Uniqueness | One canonical place per real entity | Entity-resolution review queue |
| Referential integrity | Every itinerary item references a resolved location | **Hard block** (`REQ-NFR-012`) |
| Reconciliation | Totals match source | Backfill from checkpoint |
| Drift | Price/duration distributions within bounds | Alert; recalibrate simulation |

---

## 5. Lineage

Every canonical record traces: provider payload → normalizer version → entity-resolution decision → canonical entity → evidence pack → scenario → UI component. The knowledge-graph query `KG-Q-009` ("complete evidence path from product output to source data") is the mechanism that makes this auditable rather than aspirational.

---

## 6. Status

No migration, schema or expectation file exists. Contracts are implemented in `STEP-005` (sources) and `STEP-006` (canonical model).
