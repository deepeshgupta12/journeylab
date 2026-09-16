"""The degradation drill — STEP-007 §22, §26 · TST-TRIP-002, TST-EVID-006.

WHAT §22 ASKS FOR
    "A resilience drill must prove that a degraded provider produces a refusal, not a
    partial simulation." §26 lists a **degradation drill record** among the evidence
    required to close the step.

    So this is a drill rather than a unit test: it drives the whole pipeline a real
    outage would take — `EVT-008` envelope → fold → `coverage_read_model` → cache →
    the two public operations — and asserts what a traveller is told at each stage.
    Every other test in this repository exercises one link of that chain.

WRITTEN AS A REPEATABLE TEST, NOT A ONE-OFF RECORD
    A drill performed once and written up is evidence that decays: the next change to
    the fold, the cache or the refusal path cannot be checked against a paragraph. As
    a test it runs in R1 for ever, and its record in the regression log points here.

THE FOUR STAGES
    healthy      -> accepted, no disclosure
    degraded     -> ACCEPTED with a disclosure. `REQ-EVID-006` asks for degradation to
                    be surfaced, not refused; `PUBLICATION[RECOVERING] is DEGRADED`, so
                    refusing here would turn every recovery into an outage (BUG-034)
    unavailable  -> REFUSED, with no partial anything
    recovered    -> accepted again. That stage was impossible before BUG-037: the fold
                    kept the worst state ever seen, so a region never came back
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from dbcheck import DSN, requires_db
from fastapi.testclient import TestClient
from outbox import Envelope
from projections import coverage_projection
from read_models import apply_coverage_state

REGION = "drill-bern"
ORG = "eeee0000-0000-0000-0000-00000000000e"
NOW = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)


def health(event_id: str, *, state: str, at: datetime) -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.provider.health_changed.v1",
        occurred_at=at,
        recorded_at=at,
        tenant_id=ORG,
        correlation_id="drill",
        actor=None,
        schema_version=1,
        payload_ids={
            "provider_id": "otd",
            "previous_state": "healthy",
            "new_state": state,
            "affected_regions": REGION,
        },
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    os.environ["JOURNEYLAB_DATABASE_URL"] = DSN
    import app as application

    application._COVERAGE_CACHE.invalidate()
    with TestClient(application.app) as running:
        yield running
    application._COVERAGE_CACHE.invalidate()


@pytest.fixture
def declared_region() -> Iterator[str]:
    """One declared region for the drill, removed afterwards.

    Declared here because `017` seeds none: a drill that assumed a region would pass
    only on a machine where somebody had left one behind.
    """
    with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO coverage_read_model (region_id, display_name, date_bounds_start, "
            "date_bounds_end, time_zone, freshness, accepting_trips, limitations) "
            "VALUES (%s,'Drill Bern','2026-01-01','2030-12-31','Europe/Zurich',"
            "'current',true,'[]'::jsonb) ON CONFLICT (region_id) DO UPDATE SET "
            "freshness='current', accepting_trips=true, limitations='[]'::jsonb",
            (REGION,),
        )
    try:
        yield REGION
    finally:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM coverage_read_model WHERE region_id=%s", (REGION,))


def drive(state: str, *, event_id: str, at: datetime, client: TestClient) -> None:
    """One provider transition, all the way to the read model and the cache.

    This is the pipeline under test, not a shortcut around it: the same fold, the same
    writer and the same invalidation a consumer would perform.
    """
    import app as application

    projection = coverage_projection()
    projection.consume([health(event_id, state=state, at=at)])
    with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
        apply_coverage_state(cur, projection.state)
    application._COVERAGE_CACHE.invalidate()


def trip() -> dict[str, str]:
    """A four-day trip a month out, from an explicit UTC clock.

    Not `date.today()`, which ruff's `DTZ` rules reject and this step has a reason to:
    the rule under test evaluates dates in the destination's zone, which can be a
    calendar day ahead of UTC. The month of margin is what makes the skew harmless —
    the same reasoning as `_future()` in `test_app.py`.
    """
    start = datetime.now(UTC).date() + timedelta(days=30)
    return {"start_date": start.isoformat(), "end_date": (start + timedelta(days=3)).isoformat()}


@requires_db
class TestTheDegradationDrill:
    def test_the_whole_outage_and_recovery(self, client: TestClient, declared_region: str) -> None:
        check = "/coverage:check"

        # --- 1. healthy: accepted, and nothing is disclosed that is not true ---------
        accepted = client.post(check, json={"region_id": declared_region, **trip()})
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["disclosures"] == []
        assert client.get("/coverage").json()["provider_health"] == "healthy"

        # --- 2. degraded: ACCEPTED, with the disclosure ------------------------------
        drive("degraded", event_id="drill-1", at=NOW, client=client)
        degraded = client.post(check, json={"region_id": declared_region, **trip()})
        assert degraded.status_code == 200, "a degraded region must be accepted, not refused"
        disclosures = degraded.json()["disclosures"]
        assert disclosures, "REQ-EVID-006: degradation must be surfaced"
        document = client.get("/coverage").json()
        assert document["provider_health"] == "degraded"
        assert document["observed_at"], "the answer must say when it was taken"

        # --- 3. unavailable: REFUSED, and no partial simulation ----------------------
        drive("unavailable", event_id="drill-2", at=NOW + timedelta(hours=1), client=client)
        refused = client.post(check, json={"region_id": declared_region, **trip()})
        assert refused.status_code == 503, refused.text
        assert refused.headers["content-type"].startswith("application/problem+json")
        body = refused.json()
        assert body["code"] == "coverage.provider_degraded"
        assert body["retryable"] is True, "an outage stops being true on its own"

        # THE POINT OF THE DRILL. A refusal must carry no plan, no partial plan and
        # nothing a careless client could render as one.
        for forbidden in ("nights", "itinerary", "scenario", "scenarios", "plan", "options"):
            assert forbidden not in body, f"the refusal carries {forbidden}"
        assert client.get("/coverage").json()["provider_health"] == "unavailable"

        # --- 4. recovered: accepted again --------------------------------------------
        # Impossible before BUG-037: the fold kept the worst state ever seen, so this
        # region would have stayed refused for ever, and a rebuild would not have
        # helped either.
        drive("healthy", event_id="drill-3", at=NOW + timedelta(hours=2), client=client)
        recovered = client.post(check, json={"region_id": declared_region, **trip()})
        assert recovered.status_code == 200, "the region never recovered — BUG-037"
        assert recovered.json()["disclosures"] == []
        assert client.get("/coverage").json()["provider_health"] == "healthy"

    def test_no_supplier_is_named_at_any_stage_of_the_outage(
        self, client: TestClient, declared_region: str
    ) -> None:
        """`REQ-EVID-006` forbids naming who degraded coverage. The drill is where that
        is most likely to leak, because the provider is the subject of every event."""
        for index, state in enumerate(("degraded", "unavailable", "healthy")):
            drive(
                state,
                event_id=f"drill-leak-{index}",
                at=NOW + timedelta(hours=index),
                client=client,
            )
            rendered = (
                client.get("/coverage").text
                + client.post("/coverage:check", json={"region_id": declared_region, **trip()}).text
            ).lower()
            for supplier in (
                "otd",
                "opentransportdata",
                "meteoswiss",
                "openstreetmap",
                "provider_id",
            ):
                assert supplier not in rendered, f"{supplier} leaked while {state}"
