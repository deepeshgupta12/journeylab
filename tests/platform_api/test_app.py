"""The API application — STEP-007.02.

WHAT THESE ARE PROTECTING
    The first HTTP surface in the product, and the things that go wrong quietly at
    a boundary:

      a health check that queries the database -> a brief blip restarts a process
                                                  that was fine
      a driver error rendered to a client      -> psycopg messages routinely carry
                                                  the DSN, credentials included
      an invented correlation id, silently     -> two ids in one support
                                                  conversation is worse than none
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import psycopg
import pytest
from dbcheck import DSN, requires_db
from fastapi.testclient import TestClient
from referencing.jsonschema import DRAFT202012 as DRAFT


@pytest.fixture
def client() -> Iterator[TestClient]:
    os.environ["JOURNEYLAB_DATABASE_URL"] = DSN
    import app as application

    # A fresh cache per test: the module holds one process-wide, and a document
    # cached by an earlier test would make the next one assert about stale data.
    application._COVERAGE_CACHE.invalidate()
    with TestClient(application.app) as running:
        yield running


@requires_db
class TestTheApplicationBoundary:
    def test_health_does_not_touch_the_database(self, client: TestClient) -> None:
        """A health check that queries Postgres reports the database's availability
        as the application's, so a brief blip restarts a process that was fine.
        Asserted on the source, because a passing call proves nothing here."""
        import inspect

        import app as application

        source = inspect.getsource(application.health)
        for forbidden in ("connect", "cursor", "execute", "dsn"):
            assert forbidden not in source, forbidden
        assert client.get("/api/health").json() == {"status": "ok"}

    def test_coverage_returns_the_document(self, client: TestClient) -> None:
        response = client.get("/coverage")
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"regions", "provider_health", "observed_at"}

    def test_a_supplied_correlation_id_is_echoed(self, client: TestClient) -> None:
        response = client.get("/coverage", headers={"X-Correlation-Id": "cor_from_caller"})
        assert response.headers["x-correlation-id"] == "cor_from_caller"
        assert response.headers["x-correlation-id-generated"] == "false"

    def test_a_generated_correlation_id_says_it_was_generated(self, client: TestClient) -> None:
        """Two different correlation ids in one support conversation is worse than
        none, so the response says which it handed back."""
        response = client.get("/coverage")
        assert response.headers["x-correlation-id"].startswith("cor_")
        assert response.headers["x-correlation-id-generated"] == "true"


class TestFailuresAreProblemDocuments:
    def test_a_database_failure_becomes_a_503_problem(self) -> None:
        os.environ["JOURNEYLAB_DATABASE_URL"] = (
            "postgresql://nobody:secret_password@127.0.0.1:59999/absent"
        )
        import app as application

        application._COVERAGE_CACHE.invalidate()
        with TestClient(application.app) as running:
            response = running.get("/coverage")

        assert response.status_code == 503
        assert response.headers["content-type"].startswith("application/problem+json")
        body = response.json()
        assert body["code"] == "platform.dependency_unavailable"
        assert body["retryable"] is True

        # **The DSN must not reach the client.** psycopg's message carries the
        # host, port, user and — in a misconfiguration — the password. The handler
        # deliberately does not interpolate the exception.
        rendered = response.text
        for leaked in ("secret_password", "59999", "nobody", "psycopg", "Traceback"):
            assert leaked not in rendered, leaked

    def test_the_error_code_is_registered_rather_than_invented(self) -> None:
        """`problem()` refuses an unknown code — which caught this handler using one
        that did not exist. The code was added to `ERROR_MODEL.md` and regenerated,
        because the registry is generated from the document a human reads."""
        from conventions.error_codes import ERROR_CODES

        spec = ERROR_CODES["platform.dependency_unavailable"]
        assert spec.status == 503

    def test_startup_refuses_a_missing_database_url(self) -> None:
        """No default DSN. `BUG-030` is what happens when a component decides for
        itself which database it is talking about."""
        import app as application

        saved = os.environ.pop("JOURNEYLAB_DATABASE_URL", None)
        try:
            with pytest.raises(RuntimeError, match="JOURNEYLAB_DATABASE_URL is not set"):
                application.database_url()
        finally:
            if saved is not None:
                os.environ["JOURNEYLAB_DATABASE_URL"] = saved


@requires_db
class TestTheContractIsServedAsDeclared:
    def test_the_response_validates_against_the_coverage_schema(self, client: TestClient) -> None:
        import pathlib

        import yaml
        from jsonschema import Draft202012Validator

        spec = yaml.safe_load(pathlib.Path("contracts/openapi.yaml").read_text())
        validator = Draft202012Validator(spec).evolve(
            schema=spec["components"]["schemas"]["Coverage"]
        )
        errors = [e.message for e in validator.iter_errors(client.get("/coverage").json())]
        assert errors == [], errors

    def test_the_operation_is_unauthenticated(self, client: TestClient) -> None:
        """`security: []` in the contract. A request with no credentials at all must
        succeed, because the point is learning coverage *before* signing up."""
        assert client.get("/coverage").status_code == 200

    def test_a_declared_region_reaches_the_response(self, client: TestClient) -> None:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO coverage_read_model (region_id, display_name, "
                "date_bounds_start, date_bounds_end, time_zone, freshness, "
                "accepting_trips, limitations) "
                "VALUES ('app-bern','Bern, Switzerland','2026-04-01','2027-03-31',"
                "'Europe/Zurich','degraded',true,'[\"ferry timetables are seasonal\"]') "
                "ON CONFLICT (region_id) DO NOTHING"
            )
        import app as application

        application._COVERAGE_CACHE.invalidate()
        body = client.get("/coverage").json()
        region = next(r for r in body["regions"] if r["region_id"] == "app-bern")

        assert region["display_name"] == "Bern, Switzerland"
        assert region["date_bounds"] == {"start": "2026-04-01", "end": "2027-03-31"}
        assert region["limitations"] == ["ferry timetables are seasonal"]
        assert body["provider_health"] == "degraded"
        assert "accepting_trips" not in region

        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM coverage_read_model WHERE region_id='app-bern'")
        application._COVERAGE_CACHE.invalidate()


# --- API-019, STEP-007.03 ----------------------------------------------------------

CHECK = "/coverage:check"


@pytest.fixture
def declared_region() -> Iterator[str]:
    """One region, declared for the duration of one test and then removed.

    Inserted rather than assumed: `017` seeds no region deliberately, so a test that
    relied on one already being there would pass only on a machine where somebody
    had left one behind.
    """
    region_id = "check-bern"
    with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO coverage_read_model (region_id, display_name, date_bounds_start, "
            "date_bounds_end, time_zone, freshness, accepting_trips, limitations) "
            "VALUES (%s,'Bern, Switzerland','2026-01-01','2030-12-31','Europe/Zurich',"
            "'current',true,'[]') ON CONFLICT (region_id) DO UPDATE SET freshness='current', "
            "accepting_trips=true",
            (region_id,),
        )
    try:
        yield region_id
    finally:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM coverage_read_model WHERE region_id=%s", (region_id,))


def _future(days_out: int, length: int) -> dict[str, str]:
    """A date range offset from today, in UTC.

    Not the runner's local date, and the margin is what makes that safe. The rule
    evaluates against Europe/Zurich, which can be a calendar day ahead of UTC; ±30
    days is far enough that a one-day skew cannot flip an intended future date into
    a past one. A `days_out` of 1 here would be a flaky test on half the planet.
    """
    from datetime import UTC, datetime, timedelta

    start = datetime.now(UTC).date() + timedelta(days=days_out)
    return {
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=length - 1)).isoformat(),
    }


@requires_db
class TestPlanningCheckAcceptance:
    def test_a_supported_request_is_accepted(
        self, client: TestClient, declared_region: str
    ) -> None:
        response = client.post(CHECK, json={"region_id": declared_region, **_future(30, 4)})
        assert response.status_code == 200
        body = response.json()
        assert body["region_id"] == declared_region
        assert body["display_name"] == "Bern, Switzerland"
        assert body["nights"] == 3
        assert body["disclosures"] == []

    def test_the_acceptance_validates_against_the_contract(
        self, client: TestClient, declared_region: str
    ) -> None:
        import pathlib

        import yaml
        from jsonschema import Draft202012Validator

        spec = yaml.safe_load(pathlib.Path("contracts/openapi.yaml").read_text())
        validator = Draft202012Validator(spec).evolve(
            schema=spec["components"]["schemas"]["PlanningAccepted"]
        )
        body = client.post(CHECK, json={"region_id": declared_region, **_future(30, 4)}).json()
        assert [e.message for e in validator.iter_errors(body)] == []

    def test_a_degraded_region_is_accepted_with_its_disclosure(
        self, client: TestClient, declared_region: str
    ) -> None:
        """`REQ-EVID-006` and `BUG-034`: degradation is surfaced, not refused."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE coverage_read_model SET freshness='degraded' WHERE region_id=%s",
                (declared_region,),
            )
        response = client.post(CHECK, json={"region_id": declared_region, **_future(30, 4)})
        assert response.status_code == 200
        assert response.json()["disclosures"], "a degraded region must say so"

    def test_the_operation_is_unauthenticated(
        self, client: TestClient, declared_region: str
    ) -> None:
        """`security: []`. Asking someone to register in order to be told no is the
        thing this endpoint exists not to do."""
        response = client.post(CHECK, json={"region_id": declared_region, **_future(30, 4)})
        assert response.status_code == 200


@requires_db
class TestPlanningCheckRefusals:
    """Every refusal asserts the status **and** the code.

    Status alone would pass if the handler sent 422 for everything; code alone would
    pass if a refusal were served as a 200 with a `code` field, which is precisely
    the shape `BR-061` §6 rejected.
    """

    def test_an_undeclared_region_is_refused_as_a_problem_document(
        self, client: TestClient
    ) -> None:
        response = client.post(CHECK, json={"region_id": "fr-corsica", **_future(30, 4)})
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")
        body = response.json()
        assert body["code"] == "coverage.unsupported_region"
        assert body["retryable"] is False
        assert body["status"] == 422, "RFC 9457: the member and the HTTP status must agree"

    def test_dates_outside_the_window_are_refused_with_the_bounds(
        self, client: TestClient, declared_region: str
    ) -> None:
        response = client.post(
            CHECK,
            json={
                "region_id": declared_region,
                "start_date": "2031-01-01",
                "end_date": "2031-01-04",
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "coverage.unsupported_dates"
        assert body["remediation"]["supported_dates"]["end"] == "2030-12-31"

    def test_a_trip_that_is_too_long_is_refused_with_the_range(
        self, client: TestClient, declared_region: str
    ) -> None:
        response = client.post(CHECK, json={"region_id": declared_region, **_future(30, 11)})
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "coverage.unsupported_dates"
        assert body["remediation"]["supported_trip_days"] == {"minimum": 3, "maximum": 7}

    def test_a_start_date_in_the_past_is_refused(
        self, client: TestClient, declared_region: str
    ) -> None:
        response = client.post(CHECK, json={"region_id": declared_region, **_future(-30, 4)})
        assert response.status_code == 422
        assert response.json()["code"] == "coverage.unsupported_dates"

    def test_a_suspended_region_is_refused_as_retryable(
        self, client: TestClient, declared_region: str
    ) -> None:
        """`accepting_trips=false` is how `STEP-007` §23 suspends a region.

        `retryable: true` matters here and nowhere else in this class: this refusal
        is the one that will stop being true on its own.
        """
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE coverage_read_model SET accepting_trips=false WHERE region_id=%s",
                (declared_region,),
            )
        response = client.post(CHECK, json={"region_id": declared_region, **_future(30, 4)})
        assert response.status_code == 503
        body = response.json()
        assert body["code"] == "coverage.provider_degraded"
        assert body["retryable"] is True

    def test_every_refusal_validates_against_the_problem_schema(
        self, client: TestClient, declared_region: str
    ) -> None:
        import json
        import pathlib

        import yaml
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource

        spec = yaml.safe_load(pathlib.Path("contracts/openapi.yaml").read_text())
        # `Problem.code` is `$ref: './schemas/error-codes.json'` — a deliberately
        # external, generated fragment (`ADR-012`: the enum has one source). The
        # validator needs it registered under the same relative URI the contract
        # uses, or it reports every refusal as unresolvable rather than invalid.
        codes = json.loads(pathlib.Path("contracts/schemas/error-codes.json").read_text())
        registry = Registry().with_resource(
            "./schemas/error-codes.json", Resource.from_contents(codes, default_specification=DRAFT)
        )
        validator = Draft202012Validator(spec, registry=registry).evolve(
            schema=spec["components"]["schemas"]["Problem"]
        )
        refusals = [
            {"region_id": "nowhere", **_future(30, 4)},
            {"region_id": declared_region, **_future(30, 11)},
            {"region_id": declared_region, **_future(-30, 4)},
        ]
        for payload in refusals:
            body = client.post(CHECK, json=payload).json()
            assert [e.message for e in validator.iter_errors(body)] == [], payload


@requires_db
class TestNoPartialSimulationOverHttp:
    """`REQ-TRIP-002`, asserted on the wire.

    The rule's own tests assert the type has nowhere to put a plan. These assert
    that nothing downstream adds one — a handler that helpfully attached a suggested
    itinerary would pass every test in `test_trip_request.py`.
    """

    PLAN_SHAPED = (
        "itinerary",
        "scenario",
        "scenarios",
        "options",
        "plan",
        "days",
        "activities",
        "suggested_trip",
        "alternative_trip",
        "partial",
    )

    def test_no_refusal_carries_anything_plan_shaped(
        self, client: TestClient, declared_region: str
    ) -> None:
        payloads = [
            {"region_id": "nowhere", **_future(30, 4)},
            {"region_id": declared_region, **_future(30, 11)},
            {"region_id": declared_region, "start_date": "2031-01-01", "end_date": "2031-01-04"},
        ]
        for payload in payloads:
            body = client.post(CHECK, json=payload).json()
            flat = set(body) | set(body.get("remediation") or {})
            assert not (flat & set(self.PLAN_SHAPED)), (payload, flat)

    def test_the_acceptance_carries_no_plan_either(
        self, client: TestClient, declared_region: str
    ) -> None:
        """Acceptance means *you may plan this*, not *here is the plan*. Creating a
        trip is `API-001` and it is a different operation for a reason."""
        body = client.post(CHECK, json={"region_id": declared_region, **_future(30, 4)}).json()
        assert set(body) == {"region_id", "display_name", "nights", "disclosures"}


@requires_db
class TestMalformedRequests:
    def test_an_unparseable_date_is_a_400_not_a_refusal(self, client: TestClient) -> None:
        """A malformed request is not an unsupported one. Saying "we do not cover
        those dates" for `not-a-date` would be a false statement about coverage."""
        response = client.post(
            CHECK,
            json={"region_id": "check-bern", "start_date": "not-a-date", "end_date": "2026-06-04"},
        )
        assert response.status_code in (400, 422)
        assert response.json().get("code") != "coverage.unsupported_dates"

    def test_end_before_start_is_a_400(self, client: TestClient, declared_region: str) -> None:
        response = client.post(
            CHECK,
            json={
                "region_id": declared_region,
                "start_date": "2027-06-04",
                "end_date": "2027-06-01",
            },
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation.invalid_request"

    def test_an_extra_field_is_rejected_rather_than_ignored(self, client: TestClient) -> None:
        """`additionalProperties: false`. This endpoint is unauthenticated, and a
        traveller detail silently dropped is one somebody believes was accepted."""
        response = client.post(
            CHECK,
            json={"region_id": "check-bern", **_future(30, 4), "traveller_email": "a@b.com"},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation.invalid_request"
        # The address must not come back either — it is exactly what §5 forbids.
        assert "a@b.com" not in response.text

    def test_the_request_bounds_are_the_contract_s_bounds(self) -> None:
        """Read from the contract, not restated here.

        `region_id` is `minLength: 1, maxLength: 64` in `PlanningCheckRequest`. If
        this test hardcoded 64 it would pass while the two drifted; reading the
        contract means widening one without the other fails.
        """
        import pathlib

        import yaml
        from app import REGION_ID_MAX_LENGTH, REGION_ID_MIN_LENGTH

        spec = yaml.safe_load(pathlib.Path("contracts/openapi.yaml").read_text())
        declared = spec["components"]["schemas"]["PlanningCheckRequest"]["properties"]["region_id"]
        assert declared["minLength"] == REGION_ID_MIN_LENGTH
        assert declared["maxLength"] == REGION_ID_MAX_LENGTH

    def test_an_oversized_region_id_is_rejected_rather_than_looked_up(
        self, client: TestClient
    ) -> None:
        """Unauthenticated, so an unbounded string is something anyone can send —
        and it would reach a query parameter, a log line, and a refusal message that
        quotes it back."""
        response = client.post(CHECK, json={"region_id": "x" * 500, **_future(30, 4)})
        assert response.status_code == 400
        assert response.json()["code"] == "validation.invalid_request"
        # BUG-035: FastAPI's default body includes `input` — the value that failed.
        assert "x" * 500 not in response.text, "the oversized id must not be echoed"

    def test_an_empty_region_id_is_rejected(self, client: TestClient) -> None:
        response = client.post(CHECK, json={"region_id": "", **_future(30, 4)})
        assert response.status_code == 400

    def test_a_validation_failure_is_a_problem_document(self, client: TestClient) -> None:
        """BUG-035. FastAPI's default 422 is `application/json` with a `detail`
        array and no `code`, `correlation_id` or `retryable` — so the one error
        shape `ERROR_MODEL.md` promises had an exception on the path a malformed
        request takes, and a client branching on `code` had nothing to branch on
        exactly when the request was wrong."""
        response = client.post(CHECK, json={"region_id": "ok"})
        assert response.status_code == 400
        assert response.headers["content-type"].startswith("application/problem+json")
        body = response.json()
        assert body["code"] == "validation.invalid_request"
        assert body["retryable"] is False
        assert body["correlation_id"]
        assert body["instance"] == "/coverage:check"

    def test_a_validation_failure_names_fields_and_not_their_contents(
        self, client: TestClient
    ) -> None:
        """`ERROR_MODEL.md` §5 forbids request body content in a problem document —
        it is personal data (`REQ-PRIV-004`), and on an unauthenticated endpoint it
        also reflects attacker-supplied text back to whoever reads the response."""
        secret = "this-should-never-be-echoed-back"
        response = client.post(
            CHECK,
            json={"region_id": secret, "start_date": "nope", "end_date": "also-nope"},
        )
        assert response.status_code == 400
        assert secret not in response.text
        assert "nope" not in response.text
        assert set(response.json()["remediation"]["fields"]) == {"start_date", "end_date"}

    def test_a_correlation_id_is_returned_on_a_refusal_too(self, client: TestClient) -> None:
        """The responses anyone wants to investigate are the failing ones."""
        response = client.post(
            CHECK,
            json={"region_id": "nowhere", **_future(30, 4)},
            headers={"X-Correlation-Id": "cor_refusal"},
        )
        assert response.headers["x-correlation-id"] == "cor_refusal"
        assert response.json()["correlation_id"] == "cor_refusal"
