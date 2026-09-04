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
        assert set(body) == {"regions", "provider_health"}

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
                "date_bounds_start, date_bounds_end, freshness, accepting_trips, limitations) "
                "VALUES ('app-bern','Bern, Switzerland','2026-04-01','2027-03-31',"
                "'degraded',true,'[\"ferry timetables are seasonal\"]') "
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
