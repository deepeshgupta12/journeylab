"""The API application — STEP-007.02 (ADR-003).

WHY THIS EXISTS NOW, IN A SUB-STEP ABOUT A PAGE

    `.01` built the coverage handler and `BR-059` §9 recorded that nothing routed to
    it. The page in this sub-step needs its data, and there were two ways to get it:

      read Postgres from Next.js -> `ADR-003` declares one deployable API
                                    application, and `module-boundaries.sh` already
                                    forbids `apps/web` importing `services/`. It
                                    would also duplicate the aggregate-health rule
                                    that `REQ-EVID-006` depends on, in a second
                                    language, where the two would drift.
      serve it over HTTP         -> the architecture as declared.

    So the ASGI app is a **precondition** of the page rather than scope creep, the
    same way `BUG-027`'s fix was a precondition of entity resolution. It is kept
    deliberately small: one route, one dependency, no middleware this sub-step does
    not need.

EVERY FAILURE IS A PROBLEM DOCUMENT

    `ERROR_MODEL.md` and RFC 9457. `conventions/problem.py` already refuses to build
    one containing a traceback, connection string, credential or email address — so
    the error path uses it rather than composing JSON here, where those prohibitions
    would have to be remembered.

THE CORRELATION ID IS READ, NEVER INVENTED SILENTLY

    The contract declares `CorrelationId` as a parameter on this operation. If the
    caller supplies one it is echoed; if not, one is generated **and the response
    says so**, because a support conversation that starts with two different
    correlation IDs is worse than one that starts with none.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import psycopg
from conventions.problem import problem
from fastapi import FastAPI, Header, Response
from fastapi.responses import JSONResponse
from platform_api.coverage import CoverageCache, get_coverage
from platform_api.trip_request import (
    PlanningAccepted,
    PlanningCheckError,
    check_planning_request,
    read_region,
)
from pydantic import BaseModel, ConfigDict, StrictStr

#: One process-wide cache for the one public document. Not a general-purpose cache
#: — see `platform_api.coverage.CoverageCache`, which refuses a second key.
_COVERAGE_CACHE = CoverageCache()


def database_url() -> str:
    """The database this process talks to.

    No default. `dbcheck.py` learned at STEP-001.07 that two names for one setting
    silently point halves of a system at different places; an absent value here
    fails at startup rather than connecting to a guess.
    """
    dsn = os.environ.get("JOURNEYLAB_DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError(
            "JOURNEYLAB_DATABASE_URL is not set. Refusing to fall back to a default "
            "DSN: BUG-030 is what happens when a component decides for itself which "
            "database it is talking about."
        )
    return dsn


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Fail at startup rather than on the first request.

    A process that boots without a database and reports its problem per-request
    looks healthy to an orchestrator and broken to a user.
    """
    app.state.dsn = database_url()
    yield


app = FastAPI(
    title="JourneyLab API",
    lifespan=lifespan,
    # The contract is the source of truth; this app implements it rather than
    # publishing its own derived schema, which would be a second place for the
    # shape to live.
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Liveness only. Deliberately does NOT touch the database.

    A health check that queries Postgres reports the database's availability as the
    application's, so a brief database blip restarts a process that was fine. The
    coverage endpoint is where a database failure becomes visible, and it says which
    failure it was.
    """
    return {"status": "ok"}


@app.get("/coverage")
async def coverage(
    response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> Any:
    """`API-017`. Public and unauthenticated, as the contract declares.

    No tenant is bound, and that is not an omission — see
    `platform_api.coverage`, and `BUG-028` for what happened when the read model
    assumed one.
    """
    correlation_id = x_correlation_id or f"cor_{uuid.uuid4().hex[:16]}"
    response.headers["X-Correlation-Id"] = correlation_id
    # Says so when it invented one, because two correlation IDs in one support
    # conversation are worse than none.
    response.headers["X-Correlation-Id-Generated"] = "false" if x_correlation_id else "true"

    try:
        with psycopg.connect(app.state.dsn) as conn, conn.cursor() as cur:
            document = get_coverage(cur, cache=_COVERAGE_CACHE)
    except psycopg.Error:
        # The exception is deliberately not interpolated. `safe_detail` would refuse
        # a connection string, and a psycopg error message routinely contains one.
        return JSONResponse(
            status_code=503,
            media_type="application/problem+json",
            content=problem(
                "platform.dependency_unavailable",
                correlation_id=correlation_id,
                detail="Coverage is temporarily unavailable.",
                instance="/coverage",
            ),
            headers={"X-Correlation-Id": correlation_id},
        )
    return document


class PlanningCheckBody(BaseModel):
    """`API-019` request. Closed, matching `PlanningCheckRequest`.

    `extra="forbid"` mirrors `additionalProperties: false` rather than restating it
    loosely: a field the contract forbids is rejected here too, so a client that
    sends traveller details to an unauthenticated endpoint is refused rather than
    silently having them dropped.
    """

    model_config = ConfigDict(extra="forbid")

    region_id: StrictStr
    start_date: date
    end_date: date


@app.post("/coverage:check")
async def check_planning(
    body: PlanningCheckBody,
    response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> Any:
    """`API-019`. Public and unauthenticated, as the contract declares.

    THE HANDLER DECIDES NOTHING
        Every rule lives in `platform_api.trip_request`, which takes a row and a
        clock and returns a decision. This function reads, calls, and translates the
        decision into HTTP. That split is what lets `POST /trips` (STEP-008.06)
        enforce the identical rule instead of a second copy of it — the failure
        `BUG-029` already demonstrated between a projection and a contract.

    THE CLOCK IS PASSED IN, NOT REACHED FOR
        `datetime.now(UTC)` is read here, once, and handed to the rule. The rule
        then converts it into the destination's calendar date. A rule that read the
        wall clock itself could not be tested across the boundary it exists to
        handle.
    """
    correlation_id = x_correlation_id or f"cor_{uuid.uuid4().hex[:16]}"
    response.headers["X-Correlation-Id"] = correlation_id
    response.headers["X-Correlation-Id-Generated"] = "false" if x_correlation_id else "true"

    try:
        with psycopg.connect(app.state.dsn) as conn, conn.cursor() as cur:
            region = read_region(cur, body.region_id)
    except psycopg.Error:
        # Not interpolated: a psycopg error routinely carries the DSN, and
        # `safe_detail` would refuse it — after the fact, at the point of sending.
        return _problem_response(
            "platform.dependency_unavailable",
            correlation_id=correlation_id,
            detail="Coverage is temporarily unavailable.",
        )

    try:
        decision = check_planning_request(
            region=region,
            region_id=body.region_id,
            start=body.start_date,
            end=body.end_date,
            now=datetime.now(UTC),
        )
    except PlanningCheckError as exc:
        # A malformed request, or a region whose declared zone is not a real zone.
        # Neither is a refusal: nothing was decided, so saying "we do not cover
        # those dates" would be a false statement about coverage.
        return _problem_response(
            "validation.invalid_request",
            correlation_id=correlation_id,
            detail=str(exc),
        )

    if isinstance(decision, PlanningAccepted):
        return {
            "region_id": decision.region_id,
            "display_name": decision.display_name,
            "nights": decision.nights,
            "disclosures": list(decision.disclosures),
        }

    # A refusal. The status comes from the register via the code the rule chose —
    # this handler does not know that `coverage.unsupported_dates` is a 422, and
    # keeping it that way is what stops the status drifting from `ERROR_MODEL.md`.
    return _problem_response(
        decision.code,
        correlation_id=correlation_id,
        detail=decision.reason,
        remediation=decision.remediation,
    )


def _problem_response(
    code: str,
    *,
    correlation_id: str,
    detail: str,
    remediation: dict[str, object] | None = None,
) -> JSONResponse:
    """One place where a problem document becomes a response.

    The HTTP status is taken from the document rather than passed in alongside it.
    Two consequences, both deliberate:

      * A caller cannot send `coverage.unsupported_dates` with a 200 and produce a
        refusal that reads as an acceptance. The register decides.
      * RFC 9457 requires the `status` member and the HTTP status to agree. Deriving
        one from the other makes them unable to disagree, rather than requiring two
        call sites to be kept in step.
    """
    document = problem(
        code,
        correlation_id=correlation_id,
        detail=detail,
        instance="/coverage:check",
        remediation=remediation,
    )
    return JSONResponse(
        status_code=int(document["status"]),
        media_type="application/problem+json",
        content=document,
        headers={"X-Correlation-Id": correlation_id},
    )
