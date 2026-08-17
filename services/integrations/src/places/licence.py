"""Licence records — STEP-005.02 (REQ-DATA-001, TST-DATA-001).

REQ-DATA-001: "Every provider source must have documented licence terms, permitted
cache duration and attribution obligations **before ingestion is enabled**."

WHY THIS IS A TYPE AND NOT A CHECK
    "Before ingestion is enabled" is a sequencing claim, and sequencing claims are
    kept by structure or not at all. `ingest()` takes a `LicenceRecord` — there is
    no call signature that accepts a provider without one, so the requirement
    cannot be satisfied late or forgotten under deadline.

WHY ODbL IS SINGLED OUT
    `ADR-016` chose Switzerland under an open-data-only constraint and found the
    thing that actually costs: **OpenStreetMap is ODbL, which is share-alike on
    derivative databases.** The evidence pack (`STEP-010`) is a derivative database
    on the plain reading of that licence.

    A posture — comply and publish, segregate, or prefer non-ODbL sources — is owed
    before STEP-010 and is not decided here. What IS decided here is that every
    fact carries the licence it arrived under, so that decision has something to
    act on rather than requiring an archaeology exercise across the pack.

    `Provenance.licence_id` was added in STEP-004.06 for exactly this and has had
    no user until now.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ShareAlike(enum.StrEnum):
    """Whether a derived database inherits the licence.

    Three states, not a boolean. `UNKNOWN` exists because "we have not read the
    terms" and "the terms impose nothing" are different facts, and conflating them
    is how an obligation gets discovered after the data is already in the pack.
    """

    NONE = "none"
    DERIVATIVE_DATABASE = "derivative_database"
    UNKNOWN = "unknown"


class LicenceError(Exception):
    """A licence record is missing or unusable."""


@dataclass(frozen=True, slots=True)
class LicenceRecord:
    """What REQ-DATA-001 requires, as data rather than prose."""

    licence_id: str
    source_name: str
    terms_url: str
    attribution_required: bool
    attribution_text: str
    #: Longest we may retain a copy. `None` means the terms are silent, which is
    #: NOT the same as unlimited — it is recorded as unknown and must be resolved
    #: before a retention policy claims coverage.
    max_cache_seconds: int | None
    share_alike: ShareAlike
    commercial_use_permitted: bool

    def __post_init__(self) -> None:
        if not self.licence_id.strip():
            raise LicenceError("licence_id is required")
        if not self.terms_url.startswith("https://"):
            raise LicenceError(
                f"terms_url must be an https URL so the terms can be re-read later; "
                f"got {self.terms_url!r}"
            )
        if self.attribution_required and not self.attribution_text.strip():
            raise LicenceError(
                f"{self.licence_id}: attribution is required but no attribution text "
                f"was recorded. An obligation nobody can render is an obligation nobody meets."
            )
        if not self.commercial_use_permitted:
            # Open-Meteo's free tier is the live example: CC-BY data, non-commercial
            # terms. Using it would be a licence breach rather than a rate-limit
            # problem, so the record refuses to exist rather than sitting in the
            # register waiting to be misread (ADR-016 §2).
            raise LicenceError(
                f"{self.licence_id}: commercial use is not permitted, so this source "
                f"cannot be ingested by this product at all. Recording it as a usable "
                f"licence would invite exactly the mistake ADR-016 §2 documents."
            )


#: The sources ADR-016 selected. Written here rather than in a config file because
#: adding a source is a licence decision, and a licence decision belongs in a diff.
SWISS_TRANSPORT = LicenceRecord(
    licence_id="opentransportdata.swiss",
    source_name="Open data platform mobility Switzerland",
    terms_url="https://opentransportdata.swiss/en/terms-of-use/",
    attribution_required=True,
    attribution_text="Source: opentransportdata.swiss",
    max_cache_seconds=None,
    share_alike=ShareAlike.NONE,
    commercial_use_permitted=True,
)

# DOCUMENTED FREE-TIER LIMITS — THESE ARE A COST CONTROL, NOT POLITENESS
#
#   Verified 2026-08-17 against https://opentransportdata.swiss/en/limits-and-costs/
#
#   The platform is free in two different senses, and the difference matters:
#
#       file-based data (static GTFS)   no registration, no payment at all
#       service-based data (GTFS-RT)    registration required; free BELOW the limit
#
#   Above the limit the page is explicit: "These limits can be exceeded, but then
#   costs will be incurred." Published paid tiers start at CHF 500/month.
#
#   So `ADR-016`'s zero-spend constraint is not satisfied merely by choosing this
#   provider — it is satisfied by STAYING UNDER THESE NUMBERS. That makes the
#   `TokenBucket` and `Quota` in `framework/resilience.py` a commercial control:
#   a runaway retry loop here produces an invoice, not just an annoyed provider.
#
#   Recorded as constants with their citation because a constant describing someone
#   else's system needs a citation or a test. `BUG-026` was exactly that mistake —
#   a forecast horizon justified in a comment rather than read from the provider.

#: GTFS-RT: 5 requests per minute per API key, no daily quota.
#:
#: Corroborated by two independent sources, which is why this one is trusted:
#:   - https://opentransportdata.swiss/en/limits-and-costs/
#:   - the API Manager's own plan line at subscription time, which reads
#:     "Quota: unlimited, Rate limit: 5 calls / 1 minute(s)"
SWISS_TRANSPORT_GTFS_RT_PER_MINUTE = 5

# THE SERVICE-ALERTS LIMIT WAS DISPUTED, AND IS NOW SETTLED.
#
#   Two provider pages disagreed:
#       "Limits and costs"    "GTFS RT & GTFS RT Service Alerts — 5/minute"
#       GTFS-SA cookbook      "a maximum of two requests a minute"
#
#   `REQ-EVID-002` says conflicting evidence is retained and never averaged, so both
#   were recorded and code used the lower on an asymmetry argument: under-polling
#   costs freshness we can measure, over-polling costs money.
#
#   RESOLVED 2026-08-17 by the PROVISIONED PLAN itself — `tedp_gtfs_sa_plan` reads
#   "Quota: unlimited, Rate limit: 5 calls / 1 minute(s)" in the API Manager.
#
#   That outranks both pages, and the reason is worth stating: the plan is the
#   artefact the gateway ENFORCES and bills against. A documentation page describes
#   the limit; the plan *is* the limit. The cookbook's figure is stale.
#
#   The disputed reading is kept rather than deleted. `REQ-EVID-002` retains
#   conflicts, and a conflict that has been resolved is still evidence about how
#   trustworthy each source proved to be — the cookbook was wrong once and may be
#   wrong again.

#: The stale cookbook figure. Retained as history, NOT used.
SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_STALE_DOC = 2

#: The operative limit, from the provisioned plan `tedp_gtfs_sa_plan`.
SWISS_TRANSPORT_GTFS_SA_PER_MINUTE = 5

# SEPARATE CREDENTIALS MEAN SEPARATE BUDGETS, WHICH I HAD ASSUMED OTHERWISE.
#
#   The API Manager issued one credential per product — `tedp_gtfs_rt` and
#   `tedp_gtfs_sa` — each with its own plan and its own 5/minute allowance. The
#   published limits say "per API-key", and with two keys that is two budgets.
#
#   So polling both feeds does not halve either. Each connector needs its OWN
#   `TokenBucket` sized from its own plan, and sharing one bucket across both would
#   throw away half the allowance for no reason.

#: Environment variables holding each key. Values live in `.env` (mode 600,
#: gitignored) and never in source, a log line, or a transcript.
SWISS_TRANSPORT_GTFS_RT_KEY_ENV = "JOURNEYLAB_OTD_GTFS_RT_KEY"
SWISS_TRANSPORT_GTFS_SA_KEY_ENV = "JOURNEYLAB_OTD_GTFS_SA_KEY"

#: OJP, OJPFare, Train Formation, CKAN: 50/minute and 20,000/day per key.
SWISS_TRANSPORT_OJP_PER_MINUTE = 50
SWISS_TRANSPORT_OJP_PER_DAY = 20_000

OPENSTREETMAP = LicenceRecord(
    licence_id="ODbL-1.0",
    source_name="OpenStreetMap contributors",
    terms_url="https://www.openstreetmap.org/copyright",
    attribution_required=True,
    attribution_text="© OpenStreetMap contributors",
    max_cache_seconds=None,
    # THE ONE THAT MATTERS. ADR-016 §1: the evidence pack is a derivative database
    # on the plain reading of ODbL, and a posture is owed before STEP-010.
    share_alike=ShareAlike.DERIVATIVE_DATABASE,
    commercial_use_permitted=True,
)

OPENDATA_SWISS = LicenceRecord(
    licence_id="opendata.swiss",
    source_name="Swiss open government data",
    terms_url="https://opendata.swiss/en/terms-of-use",
    attribution_required=True,
    attribution_text="Source: opendata.swiss",
    max_cache_seconds=None,
    share_alike=ShareAlike.NONE,
    commercial_use_permitted=True,
)

METEOSWISS = LicenceRecord(
    licence_id="meteoswiss",
    source_name="MeteoSwiss (Federal Office of Meteorology and Climatology)",
    terms_url="https://opendata.swiss/en/terms-of-use",
    attribution_required=True,
    attribution_text="Source: MeteoSwiss",
    max_cache_seconds=None,
    share_alike=ShareAlike.NONE,
    commercial_use_permitted=True,
)
"""The weather source ADR-016 chose, and the reason it is not Open-Meteo.

Open-Meteo publishes CC-BY data on a free tier that is **non-commercial**, so this
product cannot use it at any volume — a licence breach rather than a rate-limit
problem (ADR-016 §2). `LicenceRecord` refuses to construct a non-commercial entry
at all, so that mistake cannot be made quietly here.
"""

KNOWN_LICENCES: dict[str, LicenceRecord] = {
    record.licence_id: record
    for record in (SWISS_TRANSPORT, OPENSTREETMAP, OPENDATA_SWISS, METEOSWISS)
}


def attribution_for(licence_ids: set[str]) -> list[str]:
    """Every attribution string a rendered surface must show.

    Sorted and de-duplicated, because attribution is a product requirement rather
    than a footnote (`ADR-016`) and an unstable order makes it look like noise.
    """
    texts = {
        KNOWN_LICENCES[i].attribution_text
        for i in licence_ids
        if i in KNOWN_LICENCES and KNOWN_LICENCES[i].attribution_required
    }
    return sorted(texts)
