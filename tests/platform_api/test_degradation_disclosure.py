"""Degradation reaches the traveller — TST-EVID-006 · STEP-007.05.

THE FAILURE THIS SUB-STEP EXISTS TO PREVENT, QUOTED EXACTLY
    `REQ-EVID-006`: degradation masked by **cached data presented as current**.

    Note what it does not say. It does not forbid caching, and a test that asserted
    "the response is never cached" would be testing a rule nobody wrote while
    deleting the thing that keeps the landing page fast. The prohibition is on the
    *presented as current* half.

    So there are two independent guarantees here and both are asserted:

      the answer says when it was taken   -> a cache hit is visibly a few seconds
                                             old, so it is not presenting itself
                                             as current
      a real change busts the cache       -> the window between a provider
                                             degrading and a traveller seeing it
                                             is the write, not the TTL

    Either alone is insufficient. A timestamp with no invalidation means honest
    staleness for 30 seconds; invalidation with no timestamp means a cache hit that
    still claims to be a fresh read.
"""

from __future__ import annotations

import datetime
from typing import Any

import psycopg
import pytest
from dbcheck import DSN, requires_db
from outbox import Envelope
from platform_api.coverage import CACHE_TTL_SECONDS, CoverageCache, get_coverage
from projections import coverage_projection
from read_models import apply_coverage_state

T1 = datetime.datetime(2026, 9, 14, 8, 0, 0, tzinfo=datetime.UTC)
T2 = datetime.datetime(2026, 9, 14, 8, 0, 5, tzinfo=datetime.UTC)
ORG = "eeee0000-0000-0000-0000-00000000000e"
REGION = "disc-bern"


def health(event_id: str, *, state: str, regions: str = REGION) -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.provider.health_changed.v1",
        occurred_at=T1,
        recorded_at=T1,
        tenant_id=ORG,
        correlation_id="corr-1",
        actor=None,
        schema_version=1,
        payload_ids={"provider_id": "otd", "new_state": state, "affected_regions": regions},
    )


@pytest.fixture
def declared_region() -> Any:
    """One declared, healthy region — and removed afterwards.

    The read model is seeded with none by design (`017`), so a test about
    degradation has to declare its own subject or it is a test about an empty list.
    """
    with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO coverage_read_model (region_id, display_name, date_bounds_start, "
            "date_bounds_end, time_zone, freshness, accepting_trips, limitations) "
            "VALUES (%s,'Disclosure Bern','2026-04-01','2027-03-31','Europe/Zurich',"
            "'current',true,'[]'::jsonb) ON CONFLICT (region_id) DO NOTHING",
            (REGION,),
        )
        try:
            yield conn
        finally:
            cur.execute("DELETE FROM coverage_read_model WHERE region_id = %s", (REGION,))


# --- the timestamp half --------------------------------------------------------


@requires_db
class TestACachedAnswerSaysHowOldItIs:
    def test_a_cache_hit_returns_the_timestamp_of_the_read_that_filled_it(
        self, declared_region: Any
    ) -> None:
        """NOT the timestamp of the request.

        This is the assertion that makes `observed_at` worth having. Stamping it on
        the way out would make every cache hit claim to be a fresh read — the
        `REQ-EVID-006` defect with the field added as decoration, and it would pass
        any test that only checked the field was present.
        """
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            first = get_coverage(cur, cache=cache, observed_at=T1, now=0.0)
            # Five seconds later, still inside the TTL, a different wall clock.
            second = get_coverage(cur, cache=cache, observed_at=T2, now=5.0)

        assert first["observed_at"] == T1.isoformat()
        assert second["observed_at"] == T1.isoformat(), (
            "the cached document was re-stamped with the time of the request, so a "
            "stale answer is claiming to be a fresh one"
        )

    def test_a_read_after_expiry_carries_the_new_time(self, declared_region: Any) -> None:
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            get_coverage(cur, cache=cache, observed_at=T1, now=0.0)
            after = get_coverage(cur, cache=cache, observed_at=T2, now=CACHE_TTL_SECONDS + 1)
        assert after["observed_at"] == T2.isoformat()

    def test_every_response_carries_one_whether_degraded_or_not(self, declared_region: Any) -> None:
        """Rendering the time only when degraded would make its presence a
        degradation signal, and would leave the healthy answer — the one where a
        stale "all good" does most damage — with nothing to say how old it is.
        """
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            document = get_coverage(cur, cache=cache, observed_at=T1, now=0.0)
        assert document["provider_health"] in {"healthy", "degraded", "unavailable"}
        assert document["observed_at"] == T1.isoformat()


# --- the invalidation half -----------------------------------------------------


@requires_db
class TestDegradationReachesTheTravellerThroughTheCache:
    def test_a_health_change_is_disclosed_on_the_next_read(self, declared_region: Any) -> None:
        """The whole pipeline, end to end: event -> fold -> table -> cache -> document.

        Until STEP-007.05 this could not be written, because nothing in production
        code carried a folded projection to the table `API-017` reads.
        """
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            before = get_coverage(cur, cache=cache, observed_at=T1, now=0.0)
            assert before["provider_health"] == "healthy", "the fixture was not healthy"

            projection = coverage_projection()
            projection.consume([health("disc-e1", state="degraded")])
            changed = apply_coverage_state(cur, projection.state)

            # THE CALLER'S OBLIGATION, ASSERTED RATHER THAN ASSUMED. `changed` is
            # non-empty, so a caller that did not invalidate would be ignoring a
            # signal it was handed.
            assert changed == frozenset({REGION})
            cache.invalidate()

            after = get_coverage(cur, cache=cache, observed_at=T2, now=1.0)

        assert after["provider_health"] == "degraded"
        assert after["observed_at"] == T2.isoformat()
        region = next(r for r in after["regions"] if r["region_id"] == REGION)
        assert region["freshness"] == "degraded"
        # Straight from the read model, not composed anywhere downstream.
        assert region["limitations"] == [f"{REGION} is running on degraded sources"]

    def test_without_invalidation_the_stale_answer_still_admits_its_age(
        self, declared_region: Any
    ) -> None:
        """The negative control, and the reason both halves exist.

        A caller that ignores `changed` keeps serving the healthy answer until the
        TTL expires. That is a disclosure delay — but it is not the forbidden thing,
        because the document still carries the older `observed_at` and is therefore
        not presented as current.
        """
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            get_coverage(cur, cache=cache, observed_at=T1, now=0.0)

            projection = coverage_projection()
            projection.consume([health("disc-e2", state="unavailable")])
            apply_coverage_state(cur, projection.state)
            # Deliberately NOT invalidated.

            stale = get_coverage(cur, cache=cache, observed_at=T2, now=1.0)

        assert stale["provider_health"] == "healthy"
        assert stale["observed_at"] == T1.isoformat(), (
            "a stale cached answer must still carry the time it was taken"
        )

    def test_the_disclosure_is_within_the_lag_budget(self, declared_region: Any) -> None:
        """`CACHE_TTL_SECONDS` is the worst case a caller who ignores `changed`
        imposes. It is asserted so a change to it is a decision rather than a
        default somebody raised while tuning load."""
        assert CACHE_TTL_SECONDS <= 60, (
            "a disclosure window longer than a minute is a provider outage a "
            "traveller plans a trip through"
        )


# --- REQ-EVID-006: the response names nobody -----------------------------------


@requires_db
class TestNoSupplierReachesTheDocument:
    def test_a_degraded_document_names_no_provider(self, declared_region: Any) -> None:
        """Asserted over the whole rendered document rather than over the fields we
        remembered to check — a provider name added to `limitations` by a future
        fold would pass a field-by-field assertion."""
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            projection = coverage_projection()
            projection.consume([health("disc-e3", state="degraded")])
            apply_coverage_state(cur, projection.state)
            cache.invalidate()
            document = get_coverage(cur, cache=cache, observed_at=T2, now=0.0)

        rendered = repr(document).lower()
        for forbidden in (
            "otd",
            "opentransportdata",
            "meteoswiss",
            "openstreetmap",
            "provider_id",
            "quota",
        ):
            assert forbidden not in rendered, forbidden

    def test_provider_health_is_a_string_and_not_a_breakdown(self, declared_region: Any) -> None:
        """A list or a count reveals the supply chain's size by another route."""
        cache = CoverageCache()
        with declared_region.cursor() as cur:
            document = get_coverage(cur, cache=cache, observed_at=T1, now=0.0)
        assert isinstance(document["provider_health"], str)
