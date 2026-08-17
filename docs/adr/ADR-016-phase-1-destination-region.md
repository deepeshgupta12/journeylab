# ADR-016 — Phase 1 destination region is Switzerland

> **Status: ACCEPTED 2026-08-13.** Proposed by the implementer under `ADR-007`'s
> propose-then-confirm rule and **confirmed by the repository owner the same day**.
> Accepted ADRs are superseded, never edited.

- **Date:** 2026-08-13 · **Author:** Deepesh Kumar Gupta · **Status:** Accepted
- **Confirmed by:** Repository owner, 2026-08-13 — "ok Switzerland"
- **Constraint set by the owner, 2026-08-13:** **open data only, zero licence spend.**

## Context

`DEC-002` blocks `STEP-005` and `STEP-010` and is the last thing on the critical
path. The decision log fixes four criteria: licensability (`ASM-011`), transit data
quality, accessibility data (`ASM-020`), crowd-signal privacy (`ASM-021`).

`RISK-001` — "provider licence viability unproven", exposure 20 — is the highest
delivery risk in the register and lives entirely inside this decision.

## The research changed the shape of the question

Two findings matter more than the region ranking.

### 1. "Open data" is not "no licence constraint" — ODbL is the real risk

OpenStreetMap is the only zero-cost source of places, opening hours and
wheelchair accessibility at the coverage this product needs. It is **ODbL**, which
is **share-alike on derivative databases**.

The distinction that decides our exposure:

| | ODbL treatment |
| --- | --- |
| Rendering an itinerary to a traveller | **Produced Work** — we may license it as we like |
| **An evidence pack that stores OSM-derived POIs, hours and accessibility** | **Derivative Database** — if made available to others, it must be offered under ODbL |

The evidence pack is the core artefact of this product (`STEP-010`). An
architecture that persists enriched OSM data and serves it is, on the plain reading
of the licence, creating and publicly using a derivative database.

**This is `RISK-001` in concrete form, and it is a licence cost with no monetary
price.** Zero spend does not mean zero obligation. Three postures exist and one
must be chosen before `STEP-010`:

- **(a) Accept and comply** — publish the OSM-derived subset of the evidence pack
  under ODbL. Legally clean, and it means a competitor can take that subset.
- **(b) Segregate** — keep OSM-derived facts out of the persisted pack, resolving
  them at render time so only a Produced Work leaves the system. Architecturally
  invasive and cuts against the reproducibility `REQ-CONS-006` requires.
- **(c) Prefer non-ODbL sources** where the region provides them, and treat OSM as
  a labelled fallback whose facts are marked in provenance.

**(c) is what makes the region choice matter**, and it is why the recommendation
here is not simply "wherever the transit data is best".

### 2. The obvious weather source is unusable

Open-Meteo is CC-BY 4.0 on the data but its **free tier is explicitly
non-commercial** — private or non-profit sites without subscriptions or
advertising. JourneyLab is commercial under every `DEC-003` option. Using it free
would be a licence breach, not a rate-limit problem.

National meteorological services are the answer, and their terms vary by country —
which again ties weather to the region choice rather than being independent of it.

## Decision

**Switzerland**, as a rail-connected multi-modal region rather than a single city.

| Criterion | Switzerland |
| --- | --- |
| **Transit (`ASM-011`)** | `opentransportdata.swiss` — national GTFS covering **all operators**, plus GTFS-RT with a three-hour prediction window. Terms of use permit processing, analysis and publication, require attribution, and impose **no share-alike**. **Verified 2026-08-17:** static GTFS needs no registration and no payment; GTFS-RT needs a free key and is free **below 5 requests per minute** — above that "costs will be incurred", with paid tiers from CHF 500/month. So zero spend is satisfied by staying under the limit, not by choosing the provider, which makes the framework's rate limiter a **commercial control** |
| **Weather** | MeteoSwiss publishes via `opendata.swiss` under the same permissive Swiss open-government terms — **commercial use permitted**, avoiding the Open-Meteo trap entirely |
| **Places / hours (`ASM-011`)** | Partly `opendata.swiss` (non-ODbL, attribution-only), OSM as fallback. This is posture **(c)** above and is the weakest leg **everywhere** under zero spend |
| **Accessibility (`ASM-020`)** | Swiss public transport carries a **statutory** accessibility-information duty, so stop-level accessibility is in the official feed rather than crowd-sourced — materially better than OSM `wheelchair=*` tags alone |
| **Crowd signals (`ASM-021`)** | Official occupancy data exists in the feed, so crowding does not require observing users. **`REQ-PRIV-003` gets easier**, not harder |
| **Product fit** | Train, bus, boat, funicular, cable car, with real weather and altitude constraints. A feasibility solver has something to be *right about* |

### Why the multi-modality is the argument, not a bonus

This product exists to compare **feasible futures**. In a flat single-mode city,
almost every itinerary is feasible and the solver has nothing to prove. Switzerland
produces genuine hard constraints — last funicular, seasonal boat, weather-closed
pass — which is what makes `REQ-CONS-004` (zero hard-constraint violations) a
demonstrable claim rather than a slogan.

## Alternatives considered

| Region | Why not |
| --- | --- |
| **Netherlands** | The closest runner-up: NDOV/OVapi transit is fully open, coverage excellent, English ubiquitous, compact. Rejected only on product fit — flat, single-mode-dominant, few hard constraints for the solver to surface. **If Switzerland's cost of living skews the affiliate model, this is the fallback** |
| **Finland (Helsinki / Digitransit)** | Fully open, genuinely excellent API. Smaller scope and a shorter usable season for a 3–7 day trip |
| **Greece — Cyclades** | **Rejected, and this needs saying explicitly.** The repository's own contract examples are built on it — `solver.infeasible` names Sifnos and Antiparos ferries. **Greek ferry schedules are not published as open GTFS.** The region the documentation implicitly assumes is the one least compatible with the constraint just set. The examples are illustrative and need no change, but nobody should read them as a region decision |

## Consequences

- `STEP-005` unblocks; `STEP-005.01` (connector framework) can start immediately.
- **`RISK-001` is not closed by this.** It moves from "unproven licensability" to
  a specific, checkable question: does posture (a), (b) or (c) apply to the
  evidence pack? That decision is owed **before `STEP-010`** and should be its own
  ADR.
- Provider adapters in `STEP-005` target: `opentransportdata.swiss` (transit),
  MeteoSwiss via `opendata.swiss` (weather), `opendata.swiss` + OSM (places,
  hours, accessibility).
- Every OSM-derived fact must carry its licence in provenance. `Provenance` already
  has `licence_id` (`contracts/jsonschema/provenance.json`) — **written in
  STEP-004.06 for exactly this**, and it now has a first real user.
- Attribution is a product requirement, not a footnote: `opentransportdata.swiss`
  and MeteoSwiss must be cited wherever their data is shown.

## Other countries — what choosing one region does and does not commit us to

`PRODUCT_SCOPE` §Phase 1 is **one region, 3–7 days**; a **second destination pack
is Phase 2** (`STEP-014`, `STEP-015`, `STEP-022`). So this ADR picks the first
region, not the only one, and `CONTRACT_CHANGE_POLICY` §6 already versions
destination packs **per region with an effective date**.

That imposes a real constraint on `STEP-005`, and it is the reason this section
exists rather than being left as an aspiration:

- **No adapter may be Switzerland-shaped.** The things that make Switzerland
  attractive — a single national GTFS feed, statutory stop-level accessibility,
  official occupancy — are unusually *good*. An adapter written to assume them
  will not survive a region where accessibility is crowd-sourced and occupancy
  does not exist.
- **Absence must be representable.** The Netherlands fallback has no statutory
  accessibility duty; a pack that cannot say "this region has no official
  accessibility source" will force the second region to fake one.
- **The licence differs per source, so it belongs in the data.**
  `Provenance.licence_id` already exists for this. Switzerland's attribution-only
  terms and OSM's ODbL will coexist inside one pack from day one, so the field is
  load-bearing immediately rather than in Phase 2.

The concrete test: **adding the Netherlands should be a new pack and new adapter
configuration, not a change to the connector framework.** If it is not, the
framework is wrong, and `STEP-005.01` is where that is decided.

## What this ADR does not decide

The ODbL posture (a/b/c), the precise city corridor, whether a paid feed is ever
revisited, and **when** the second region lands. Each is separable and none blocks
`STEP-005.01`.

## Review trigger

The ODbL posture decision forces a different sourcing strategy; or Swiss cost of
living proves incompatible with the `DEC-003` business model, in which case the
Netherlands is the prepared fallback.

---

## Related
- [DEC-002](../product/02-delivery/DECISION_LOG.md) — the decision this proposes to close
- [ADR-007](ADR-007-decisions-resolved-just-in-time.md) — the propose-then-confirm rule this follows
- [RISK-001](../product/01-product/RISK_REGISTER.md) — provider licence viability
- [STEP-005](../product/08-steps/STEP-005-source-integrations-and-ingestion.md) — unblocked by this
