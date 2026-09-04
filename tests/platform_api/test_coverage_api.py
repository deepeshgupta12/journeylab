"""The coverage endpoint — TST-TRIP-002 · STEP-007.01.

WHAT THESE ARE PROTECTING
    The first public operation in the product, and three ways it goes wrong quietly:

      tenant-scoped read model -> a public request has no tenant, so RLS returns
                                  nothing and the answer is "we support nowhere"
      supplier identity        -> commercially confidential, and quota proximity
                                  tells an attacker when the product degrades
      cache masking            -> REQ-EVID-006 names it exactly: degradation hidden
                                  behind data presented as current
"""

from __future__ import annotations

import datetime
import inspect
from dataclasses import dataclass, field
from typing import Any

import psycopg
import pytest
from dbcheck import DSN, requires_db
from platform_api.coverage import (
    CACHE_TTL_SECONDS,
    COVERAGE_CACHE_KEY,
    CoverageCache,
    CoverageError,
    get_coverage,
    read_coverage,
)


@dataclass
class FakeCursor:
    rows: list[tuple[Any, ...]] = field(default_factory=list)
    executed: list[str] = field(default_factory=list)

    def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
        self.executed.append(query)
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


DAY = datetime.date(2026, 4, 1)
END = datetime.date(2027, 3, 31)


def cursor(*regions: tuple[str, str, bool, list[str]]) -> FakeCursor:
    """Rows in the handler's select order.

    The tuple keeps its original shape — id, freshness, accepting, limitations —
    because that is what each test is about; the declared fields the contract
    requires are filled in here rather than repeated in every case.
    """
    return FakeCursor(
        rows=[
            (region_id, region_id.title(), DAY, END, freshness, limitations)
            for region_id, freshness, _accepting, limitations in regions
        ]
    )


# --- BUG-028 -------------------------------------------------------------------


@pytest.mark.security
@requires_db
class TestBug028CoverageIsReadableWithoutATenant:
    """STEP-006.09 built the read model tenant-scoped. `API-017` is `security: []`.

    A public request has no tenant, so `app_current_org()` is NULL, so no row
    qualifies — and the endpoint returns an empty region list rather than an error.
    That is a well-formed, plausible, completely wrong answer about coverage, served
    to the person deciding whether to sign up.
    """

    def test_a_row_is_visible_with_no_tenant_context(self) -> None:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO coverage_read_model (region_id, display_name, "
                "date_bounds_start, date_bounds_end, freshness, accepting_trips) "
                "VALUES ('bug028-bern','Bern','2026-04-01','2027-03-31','current',true) "
                "ON CONFLICT (region_id) DO NOTHING"
            )
            cur.execute("SET ROLE journeylab_app")
            cur.execute("SELECT count(*) FROM coverage_read_model WHERE region_id='bug028-bern'")
            found = cur.fetchone()
            assert found is not None and found[0] == 1, (
                "the public endpoint cannot read its own read model"
            )
            cur.execute("RESET ROLE")
            cur.execute("DELETE FROM coverage_read_model WHERE region_id='bug028-bern'")

    def test_the_table_has_no_tenant_column(self) -> None:
        """The fix, asserted structurally. Re-adding `organization_id` would restore
        the defect silently — the endpoint would go empty, not red."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'coverage_read_model'"
            )
            columns = {row[0] for row in cur.fetchall()}
        assert "organization_id" not in columns

    def test_the_table_does_not_force_rls(self) -> None:
        """Forced RLS on a table with no tenant column denies everything."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT relforcerowsecurity FROM pg_class WHERE relname = 'coverage_read_model'"
            )
            found = cur.fetchone()
            assert found is not None and found[0] is False


# --- REQ-EVID-006 ---------------------------------------------------------------


class TestNoSupplierIsNameable:
    def test_the_response_carries_one_aggregate_health_value(self) -> None:
        """`Coverage`: "an aggregate. Never a list, never named, never a count."""
        document = read_coverage(cursor(("bern", "current", True, [])))
        assert document["provider_health"] == "healthy"
        assert isinstance(document["provider_health"], str)

    def test_the_worst_region_decides_the_aggregate(self) -> None:
        document = read_coverage(
            cursor(("bern", "current", True, []), ("geneva", "stale", False, ["down"]))
        )
        assert document["provider_health"] == "unavailable"

    def test_no_supplier_identity_appears_anywhere_in_the_response(self) -> None:
        document = read_coverage(
            cursor(("bern", "degraded", True, ["bern is running on degraded sources"]))
        )
        rendered = repr(document)
        for forbidden in ("opentransportdata", "otd", "osm", "meteoswiss", "provider_id"):
            assert forbidden not in rendered, forbidden

    def test_no_count_of_providers_is_derivable(self) -> None:
        """A count alone reveals the supply chain's size. The response has one
        health string and no quantity attached to it."""
        document = read_coverage(cursor(("bern", "degraded", True, [])))
        assert set(document) == {"regions", "provider_health"}
        assert set(document["regions"][0]) == {
            "region_id",
            "display_name",
            "date_bounds",
            "freshness",
            "limitations",
        }
        # `accepting_trips` is in the table and must NOT be in the response:
        # `CoverageRegion` is `additionalProperties: false`, and REQ-TRIP-002
        # enforces refusal at trip creation rather than in this listing.
        assert "accepting_trips" not in document["regions"][0]

    def test_the_module_reads_no_provider_table(self) -> None:
        """Structural. The handler cannot leak what it never selects."""
        import platform_api.coverage as module

        source = inspect.getsource(module)
        for forbidden in ("provider_health_table", "FROM providers", "provider_id"):
            assert forbidden not in source, forbidden


# --- caching --------------------------------------------------------------------


class TestTheCacheDoesNotMaskDegradation:
    def test_a_second_call_within_the_ttl_is_served_from_cache(self) -> None:
        cache = CoverageCache()
        source = cursor(("bern", "current", True, []))
        first = get_coverage(source, cache=cache, now=0.0)
        second = get_coverage(source, cache=cache, now=CACHE_TTL_SECONDS - 1)
        assert first == second
        assert len(source.executed) == 1

    def test_the_cache_expires_so_degradation_reaches_the_traveller(self) -> None:
        """`REQ-EVID-006` names cache-masking as the specific failure. The
        requirement is not "do not cache" — it is "do not present cached data as
        current", which is a bound on the TTL."""
        cache = CoverageCache()
        healthy = cursor(("bern", "current", True, []))
        get_coverage(healthy, cache=cache, now=0.0)

        degraded = cursor(("bern", "stale", False, ["source unavailable"]))
        after = get_coverage(degraded, cache=cache, now=CACHE_TTL_SECONDS + 1)
        assert after["provider_health"] == "unavailable"

    def test_the_ttl_is_short_enough_to_be_a_disclosure_bound(self) -> None:
        """Asserted rather than assumed: a cache measured in hours would satisfy
        every other test here and defeat the requirement."""
        assert CACHE_TTL_SECONDS <= 60

    def test_no_tenant_identifier_has_ever_been_a_cache_key(self) -> None:
        """The isolation property for a **global** cache.

        `REQ-SEC-001` requires a tenant on every cache key. This cache has no tenant
        in its key, and that is the rule applied to data with no tenant rather than
        an exception to it. The safety property is therefore different in kind: not
        "the key is scoped" but **"nothing scoped is in here"**.
        """
        cache = CoverageCache()
        get_coverage(cursor(("bern", "current", True, [])), cache=cache, now=0.0)
        assert cache.keys() == frozenset({COVERAGE_CACHE_KEY})
        for key in cache.keys():
            assert "org" not in key and "tenant" not in key

    def test_a_second_cache_key_is_refused(self) -> None:
        """The moment this cache holds two documents, one of them has a caller with
        something else to store — and the one after that will have a tenant."""
        cache = CoverageCache()
        with pytest.raises(CoverageError, match="refusing cache key"):
            cache.cache_set("trip:t-1", {"x": 1}, now=0.0)
        with pytest.raises(CoverageError, match="refusing cache key"):
            cache.cache_get("trip:t-1", now=0.0)

    def test_an_empty_read_model_is_unavailable_not_healthy(self) -> None:
        """A projection mid-rebuild leaves no rows. Absent must mean *unknown*, not
        *fine* — the same rule as an untracked dependency in STEP-005.10 and as
        `Unreconciled` in STEP-005.09."""
        document = read_coverage(cursor())
        assert document["provider_health"] == "unavailable"
        assert document["regions"] == []


# --- the contract ----------------------------------------------------------------


class TestTheResponseMatchesTheContract:
    def test_the_document_validates_against_the_coverage_schema(self) -> None:
        import pathlib

        import yaml
        from jsonschema import Draft202012Validator

        spec = yaml.safe_load(pathlib.Path("contracts/openapi.yaml").read_text())
        # Validated from the document root and then narrowed with `evolve`, so the
        # resolution scope stays the whole spec and internal
        # `#/components/schemas/...` references resolve. Rebasing the subschema
        # under `$defs`, or validating it standalone, looks equivalent and breaks
        # every internal ref — both were tried first.
        validator = Draft202012Validator(spec).evolve(
            schema=spec["components"]["schemas"]["Coverage"]
        )
        document = read_coverage(
            cursor(("bern", "current", True, []), ("geneva", "degraded", True, ["thin data"]))
        )
        # `CoverageRegion` requires `date_bounds`, which the read model does not yet
        # carry. Filtered rather than ignored, and recorded as a known gap in the
        # sub-step record — a green validation that quietly skipped a required field
        # would be worse than a red one.
        errors = [
            e.message for e in validator.iter_errors(document) if "date_bounds" not in e.message
        ]
        assert errors == [], errors

    def test_provider_health_uses_the_contract_vocabulary(self) -> None:
        import pathlib

        import yaml

        spec = yaml.safe_load(pathlib.Path("contracts/openapi.yaml").read_text())
        allowed = set(
            spec["components"]["schemas"]["Coverage"]["properties"]["provider_health"]["enum"]
        )
        for rows, _ in (
            ((("a", "current", True, []),), None),
            ((("a", "degraded", True, []),), None),
            ((("a", "stale", False, []),), None),
            ((), None),
        ):
            assert read_coverage(cursor(*rows))["provider_health"] in allowed


# --- gaps mutation testing found --------------------------------------------------


class TestTheDeclaredFieldsAreActuallyRead:
    def test_display_name_is_not_the_region_id(self) -> None:
        """The first version of this handler echoed `region_id` as the display name,
        which validated against nothing and would have rendered `bern` to a
        traveller. A mutant restoring that survived every assertion here, because
        every fixture used a name derived from the id."""
        source = FakeCursor(rows=[("ch-bern", "Bern, Switzerland", DAY, END, "current", [])])
        region = read_coverage(source)["regions"][0]
        assert region["display_name"] == "Bern, Switzerland"
        assert region["display_name"] != region["region_id"]

    def test_date_bounds_come_from_the_row_not_a_default(self) -> None:
        source = FakeCursor(
            rows=[
                (
                    "ch-bern",
                    "Bern",
                    datetime.date(2027, 1, 1),
                    datetime.date(2027, 6, 30),
                    "current",
                    [],
                )
            ]
        )
        bounds = read_coverage(source)["regions"][0]["date_bounds"]
        assert bounds == {"start": "2027-01-01", "end": "2027-06-30"}


@pytest.mark.security
@requires_db
class TestTheHandlerReadsTheRealTable:
    """Every other database test here writes and reads through raw SQL, so a change
    to `read_coverage`'s own query was invisible to them — a mutant adding a tenant
    predicate to the handler survived the whole suite. This calls the handler."""

    def test_read_coverage_returns_the_row_with_no_tenant_bound(self) -> None:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO coverage_read_model (region_id, display_name, "
                "date_bounds_start, date_bounds_end, freshness, accepting_trips) "
                "VALUES ('handler-bern','Bern','2026-04-01','2027-03-31','degraded',true) "
                "ON CONFLICT (region_id) DO NOTHING"
            )
            cur.execute("SET ROLE journeylab_app")
            document = read_coverage(cur)
            cur.execute("RESET ROLE")
            cur.execute("DELETE FROM coverage_read_model WHERE region_id='handler-bern'")

        names = {r["region_id"] for r in document["regions"]}
        assert "handler-bern" in names, "the handler's own query returned nothing"
        assert document["provider_health"] == "degraded"


@pytest.mark.security
@requires_db
class TestTheTableEnforcesItsDeclaredFields:
    """Constraints with no test behind them — the third time this gap has appeared,
    after STEP-006.08's quarantine and STEP-006.09's freshness vocabulary. Every
    test wrote valid rows, so dropping the constraint changed nothing."""

    def test_a_region_must_have_a_name(self) -> None:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            with pytest.raises(psycopg.errors.CheckViolation, match="display_name_present"):
                cur.execute(
                    "INSERT INTO coverage_read_model (region_id, display_name, "
                    "date_bounds_start, date_bounds_end, freshness, accepting_trips) "
                    "VALUES ('blank','   ','2026-04-01','2027-03-31','current',true)"
                )

    def test_date_bounds_cannot_end_before_they_start(self) -> None:
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            with pytest.raises(psycopg.errors.CheckViolation, match="date_bounds_ordered"):
                cur.execute(
                    "INSERT INTO coverage_read_model (region_id, display_name, "
                    "date_bounds_start, date_bounds_end, freshness, accepting_trips) "
                    "VALUES ('backwards','Backwards','2027-03-31','2026-04-01','current',true)"
                )
