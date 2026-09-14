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
from conventions.concurrency import IdempotencyError, require_idempotency_key
from conventions.problem import problem
from fastapi import FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from platform_api.coverage import CoverageCache, get_coverage
from platform_api.trip_request import (
    PlanningAccepted,
    PlanningCheckError,
    check_planning_request,
    read_region,
)
from platform_api.waitlist import (
    EMAIL_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
    REGION_QUERY_MAX_LENGTH,
    WaitlistError,
    join_waitlist,
    withdraw_waitlist_consent,
)
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

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


@app.exception_handler(RequestValidationError)
async def validation_problem(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Every failure is a problem document, including the ones FastAPI raises.

    WHAT WAS WRONG (BUG-035)
        FastAPI's default handler returns `application/json` with a `detail` array
        and **no `code`, no `correlation_id`, no `retryable`** — so the one shape
        `ERROR_MODEL.md` promises had an exception nobody had noticed, on the path a
        malformed request takes. A client branching on `code` sees nothing to branch
        on precisely when the request was wrong.

    THE OFFENDING VALUES ARE NAMED, NEVER ECHOED
        The default body includes `input` — the value that failed. `ERROR_MODEL.md`
        §5 forbids request body content in a problem document, because constraints
        and free text are personal data (`REQ-PRIV-004`), and on an unauthenticated
        endpoint it also reflects arbitrary attacker-supplied text back to whoever
        reads the response.

        So this names the **fields** and not their contents, which is exactly what
        the register's remediation for this code asks for: "show the offending
        fields inline".
    """
    correlation_id = request.headers.get("X-Correlation-Id") or f"cor_{uuid.uuid4().hex[:16]}"
    fields = sorted(
        {
            ".".join(str(part) for part in error.get("loc", ()) if part != "body")
            for error in exc.errors()
        }
        - {""}
    )
    document = problem(
        "validation.invalid_request",
        correlation_id=correlation_id,
        detail="The request does not match the contract for this operation.",
        instance=request.url.path,
        remediation={"kind": "correct_fields", "fields": fields},
    )
    return JSONResponse(
        status_code=int(document["status"]),
        media_type="application/problem+json",
        content=document,
        headers={"X-Correlation-Id": correlation_id},
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


#: Bounds on `region_id`, mirroring `PlanningCheckRequest` in the contract.
#:
#: `maxLength` is the one that earns its place. This operation is unauthenticated,
#: so an unbounded string is something anyone can send, and it reaches a query
#: parameter, a log line and a refusal message that quotes it back. A region id is a
#: slug; 64 characters is generous for one.
REGION_ID_MIN_LENGTH = 1
REGION_ID_MAX_LENGTH = 64


class PlanningCheckBody(BaseModel):
    """`API-019` request. Closed, matching `PlanningCheckRequest`.

    `extra="forbid"` mirrors `additionalProperties: false` rather than restating it
    loosely: a field the contract forbids is rejected here too, so a client that
    sends traveller details to an unauthenticated endpoint is refused rather than
    silently having them dropped.

    The length bounds are mirrored the same way, and a test reads both numbers **out
    of the contract** rather than restating them — a constraint declared in one place
    and enforced in another is two places for it to live.
    """

    model_config = ConfigDict(extra="forbid")

    region_id: StrictStr = Field(min_length=REGION_ID_MIN_LENGTH, max_length=REGION_ID_MAX_LENGTH)
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
            instance="/coverage:check",
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
            instance="/coverage:check",
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
        instance="/coverage:check",
        remediation=decision.remediation,
    )


class WaitlistConsentBody(BaseModel):
    """`API-020` consent block. Closed, matching `WaitlistConsent`.

    `granted` has **no default**, here or in the contract or in the database. A
    default of `true` is a pre-ticked box written in Python; a default of `false` is
    a field clients quietly stop sending. Requiring it is what makes the grant an
    action somebody took.
    """

    model_config = ConfigDict(extra="forbid")

    purpose: StrictStr
    #: `StrictBool`, so `"true"`, `1` and `"yes"` are refused rather than coerced.
    #: A truthy string arriving where a consent decision belongs is exactly the kind
    #: of accident that should fail loudly.
    granted: StrictBool


class WaitlistJoinBody(BaseModel):
    """`API-020` request. Closed, matching `WaitlistJoinRequest`.

    The length bounds are the module's constants rather than literals, so the schema,
    the rule and the database cannot drift apart — the same argument
    `PlanningCheckBody` makes about `region_id`.
    """

    model_config = ConfigDict(extra="forbid")

    email: StrictStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=EMAIL_MAX_LENGTH)
    region_query: StrictStr | None = Field(default=None, max_length=REGION_QUERY_MAX_LENGTH)
    consent: WaitlistConsentBody


class WaitlistWithdrawBody(BaseModel):
    """`API-020` withdrawal request. The token is the entire authorisation."""

    model_config = ConfigDict(extra="forbid")

    withdrawal_token: StrictStr = Field(min_length=16, max_length=128)


@app.post("/waitlist", status_code=201)
async def join_the_waitlist(
    body: WaitlistJoinBody,
    request: Request,
    response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> Any:
    """`API-020`. Public, unauthenticated, and the first operation that writes
    personal data belonging to somebody with no account.

    THE HANDLER DECIDES NOTHING, AGAIN
        Validation, the consent rule and the SQL all live in `platform_api.waitlist`.
        This function reads headers, calls, and translates. `POST /trips`
        (STEP-008.06) and the account consent screen (STEP-008.04) will need the
        same rules, and a copy here is how `BUG-029` happened.

    NOTHING IS LOGGED
        No log line, no trace attribute, no event. The address is personal data from
        the moment it is typed (§8), and this handler holds it only long enough to
        pass it to the rule.
    """
    correlation_id = x_correlation_id or f"cor_{uuid.uuid4().hex[:16]}"
    response.headers["X-Correlation-Id"] = correlation_id
    response.headers["X-Correlation-Id-Generated"] = "false" if x_correlation_id else "true"

    try:
        require_idempotency_key(dict(request.headers))
    except IdempotencyError as exc:
        # The contract declares the parameter; this enforces it. A form that
        # double-submits without a key would otherwise rotate its own token, which
        # is harmless but indistinguishable from the case that is not.
        return _problem_response(
            "validation.invalid_request",
            correlation_id=correlation_id,
            detail=str(exc),
            instance="/waitlist",
            remediation={"kind": "correct_fields", "fields": ["Idempotency-Key"]},
        )

    try:
        with psycopg.connect(app.state.dsn) as conn, conn.cursor() as cur:
            try:
                grant = join_waitlist(
                    cur,
                    email=body.email,
                    region_query=body.region_query,
                    purpose=body.consent.purpose,
                    granted=body.consent.granted,
                    now=datetime.now(UTC),
                )
            except WaitlistError as exc:
                # Rolled back rather than committed: a refused request must leave no
                # row, which is what makes "no entry without consent" a property of
                # the code rather than a claim about it.
                conn.rollback()
                return _problem_response(
                    "validation.invalid_request",
                    correlation_id=correlation_id,
                    # `str(exc)` names fields, never values — see `WaitlistError`.
                    detail=str(exc),
                    instance="/waitlist",
                    remediation={"kind": "correct_fields", "fields": list(exc.fields)},
                )
            conn.commit()
    except psycopg.Error:
        # Not interpolated: a psycopg error routinely carries the DSN, and on this
        # operation it can also carry the row it failed to write — which contains an
        # email address.
        return _problem_response(
            "platform.dependency_unavailable",
            correlation_id=correlation_id,
            detail="The waitlist is temporarily unavailable.",
            instance="/waitlist",
        )

    return {
        "purpose": grant.purpose,
        "basis": grant.basis,
        "granted_at": grant.granted_at.isoformat(),
        "withdrawal_token": grant.withdrawal_token,
    }


@app.post("/waitlist:withdraw")
async def withdraw_from_the_waitlist(
    body: WaitlistWithdrawBody,
    request: Request,
    response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> Any:
    """`API-020`. Withdraw one purpose and delete the address it was granted with.

    AN UNKNOWN TOKEN IS `authz.forbidden`, WHOSE REGISTER ENTRY READS
    "Identical to not-found"
        Returning a distinguishable 404 would make this an oracle for whether a
        token ever existed. The code is reused rather than a new one invented,
        because the register had already decided this exact question.
    """
    correlation_id = x_correlation_id or f"cor_{uuid.uuid4().hex[:16]}"
    response.headers["X-Correlation-Id"] = correlation_id
    response.headers["X-Correlation-Id-Generated"] = "false" if x_correlation_id else "true"

    try:
        require_idempotency_key(dict(request.headers))
    except IdempotencyError as exc:
        return _problem_response(
            "validation.invalid_request",
            correlation_id=correlation_id,
            detail=str(exc),
            instance="/waitlist:withdraw",
            remediation={"kind": "correct_fields", "fields": ["Idempotency-Key"]},
        )

    try:
        with psycopg.connect(app.state.dsn) as conn, conn.cursor() as cur:
            withdrawal = withdraw_waitlist_consent(
                cur,
                token=body.withdrawal_token,
                now=datetime.now(UTC),
            )
            conn.commit()
    except psycopg.Error:
        return _problem_response(
            "platform.dependency_unavailable",
            correlation_id=correlation_id,
            detail="The waitlist is temporarily unavailable.",
            instance="/waitlist:withdraw",
        )

    if withdrawal is None:
        # 404, NOT the register's default 403 for this code — `NotFoundOrForbidden`.
        #
        # The contract forbids a bare 403 anywhere, and the reason applies exactly
        # here: a 403 discloses that there is something there to be forbidden. A
        # token that never existed and a token belonging to somebody else must be
        # indistinguishable, or this endpoint becomes an oracle for which tokens
        # have been issued.
        return _problem_response(
            "authz.forbidden",
            correlation_id=correlation_id,
            detail="That withdrawal token does not authorise anything.",
            instance="/waitlist:withdraw",
            status=404,
        )

    # A repeat withdrawal is a success. The state the caller asked for is the state
    # that holds, and `changed` is deliberately not in the response: telling a
    # caller "you already did this" is information about the record, and this
    # operation exists to remove information about the record.
    return {
        "purpose": withdrawal.purpose,
        "withdrawn_at": withdrawal.withdrawn_at.isoformat(),
    }


def _problem_response(
    code: str,
    *,
    correlation_id: str,
    detail: str,
    instance: str,
    remediation: dict[str, object] | None = None,
    status: int | None = None,
) -> JSONResponse:
    """One place where a problem document becomes a response.

    The HTTP status is taken from the document rather than passed in alongside it.
    Two consequences, both deliberate:

      * A caller cannot send `coverage.unsupported_dates` with a 200 and produce a
        refusal that reads as an acceptance. The register decides.
      * RFC 9457 requires the `status` member and the HTTP status to agree. Deriving
        one from the other makes them unable to disagree, rather than requiring two
        call sites to be kept in step.

    `instance` became a parameter at STEP-007.04, when a second operation started
    using this. It was hardcoded to `/coverage:check` — correct while there was one
    caller, and a wrong `instance` on every waitlist problem the moment there were
    two. Required rather than defaulted: a default would have been the same bug
    with a longer fuse.
    """
    document = problem(
        code,
        correlation_id=correlation_id,
        detail=detail,
        instance=instance,
        remediation=remediation,
        # Almost always None, so the register decides. The one caller that passes it
        # is the withdrawal denial, where the contract's shared `NotFoundOrForbidden`
        # deliberately answers 404 for a code the register statuses at 403.
        status=status,
    )
    return JSONResponse(
        status_code=int(document["status"]),
        media_type="application/problem+json",
        content=document,
        headers={"X-Correlation-Id": correlation_id},
    )
