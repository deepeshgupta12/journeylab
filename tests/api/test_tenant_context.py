"""Tenant/actor context resolution — TST-SEC-001, TST-SEC-004 · STEP-002.02.

These tests carry the same obligation as the STEP-002.01 isolation suite: each one
must be able to FAIL. Several therefore build a deliberately vulnerable
implementation and assert the same check catches it. A security test that has never
been shown to fail is a claim, not evidence (BUG-001, BUG-004, BUG-007).

The database test is integration and needs the local stack; it SKIPS when the stack
is down. A skip is not a pass and is reported as a skip.
"""

# NOTE: deliberately NO `from __future__ import annotations` here.
# PEP 563 turns annotations into strings, and FastAPI resolves them with
# get_type_hints() against MODULE globals. `Annotated[RequestContext,
# Depends(dependency)]` where `dependency` is a LOCAL of build_app then fails to
# resolve, and FastAPI silently reinterprets the parameter as a request field —
# every route returns 422 instead of using the dependency. Relevant to STEP-004.

import asyncio
import uuid
from typing import Annotated

import pytest
from auth import (
    RequestContext,
    TokenClaims,
    TokenError,
    bind_tenant,
    make_context_dependency,
    opaque_denial,
    stamp_envelope,
)
from auth.dependencies import ContextDependency
from dbcheck import DSN, requires_db
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

ORG_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
ORG_B = uuid.UUID("22222222-2222-2222-2222-222222222222")
USER_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
# BUG-024: the seed helper needs a second user; these UUIDs match the ones
# tests/security/test_tenant_isolation.sh uses, so the two suites agree rather
# than fighting over the same organizations with different members.
USER_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# Not a credential: an opaque string the stub recognises. S105 flags the literal
# comparison, so it is named once here rather than suppressed at each use.
VALID_TOKEN = "valid-token-for-org-a"


class StubVerifier:
    """Test double for the DEC-004 verifier port. Accepts exactly one token."""

    def verify(self, raw_token: str) -> TokenClaims:
        if raw_token != VALID_TOKEN:
            raise TokenError("unverified")
        return TokenClaims(subject=USER_A, organization_id=ORG_A)


def build_app(dependency: ContextDependency) -> FastAPI:
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(ctx: Annotated[RequestContext, Depends(dependency)]) -> dict[str, str]:
        return {"org": str(ctx.organization_id), "actor": str(ctx.actor_id)}

    @app.get("/missing")
    async def missing() -> dict[str, str]:
        # A resource that genuinely does not exist, raising the same denial.
        raise opaque_denial()

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(
        build_app(make_context_dependency(StubVerifier())), raise_server_exceptions=False
    )


# --- TST-SEC-004: fail closed ------------------------------------------------


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="no-authorization-header"),
        pytest.param({"Authorization": ""}, id="empty-header"),
        pytest.param({"Authorization": "valid-token-for-org-a"}, id="no-bearer-scheme"),
        pytest.param({"Authorization": "Basic dXNlcjpwYXNz"}, id="wrong-scheme"),
        pytest.param({"Authorization": "Bearer "}, id="bearer-with-no-token"),
        pytest.param({"Authorization": "Bearer wrong"}, id="unverifiable-token"),
    ],
)
def test_request_without_resolvable_context_is_rejected(
    client: TestClient, headers: dict[str, str]
) -> None:
    assert client.get("/whoami", headers=headers).status_code == 404


def test_valid_token_resolves_context(client: TestClient) -> None:
    r = client.get("/whoami", headers={"Authorization": "Bearer valid-token-for-org-a"})
    assert r.status_code == 200
    assert r.json() == {"org": str(ORG_A), "actor": str(USER_A)}


# --- the tenant comes from the token, and only the token ---------------------


@pytest.mark.parametrize(
    "hint",
    [
        {"X-Tenant-Id": str(ORG_B)},
        {"X-Organization-Id": str(ORG_B)},
        {"X-Tenant-Id": str(ORG_B), "X-Forwarded-Tenant": str(ORG_B)},
    ],
)
def test_client_supplied_tenant_hints_are_ignored(client: TestClient, hint: dict[str, str]) -> None:
    r = client.get("/whoami", headers={"Authorization": "Bearer valid-token-for-org-a", **hint})
    assert r.status_code == 200
    assert r.json()["org"] == str(ORG_A), "client hint overrode the token's tenant"


def test_query_and_body_cannot_influence_tenant(client: TestClient) -> None:
    r = client.get(
        f"/whoami?org={ORG_B}&organization_id={ORG_B}",
        headers={"Authorization": "Bearer valid-token-for-org-a"},
    )
    assert r.json()["org"] == str(ORG_A)


def test_the_hint_test_can_actually_fail() -> None:
    """META-TEST: prove the assertion above catches a header-trusting implementation.

    Without this, `test_client_supplied_tenant_hints_are_ignored` passes for a
    trivial reason — the implementation happens not to look at headers — and would
    keep passing if someone later added a "convenience" override.
    """

    async def vulnerable(request: Request) -> RequestContext:
        hinted = request.headers.get("x-tenant-id")
        return RequestContext(
            actor_id=USER_A,
            organization_id=uuid.UUID(hinted) if hinted else ORG_A,
        )

    vulnerable_client = TestClient(build_app(vulnerable), raise_server_exceptions=False)
    r = vulnerable_client.get(
        "/whoami",
        headers={"Authorization": "Bearer valid-token-for-org-a", "X-Tenant-Id": str(ORG_B)},
    )
    assert r.json()["org"] == str(ORG_B), (
        "the vulnerable implementation did NOT honour the header, so the real test "
        "above proves nothing about header trust"
    )


# --- REQ-SEC-004: denial is indistinguishable from absence -------------------


def test_denied_and_missing_are_byte_identical(client: TestClient) -> None:
    denied = client.get("/whoami")
    missing = client.get("/missing", headers={"Authorization": "Bearer valid-token-for-org-a"})

    assert denied.status_code == missing.status_code
    assert denied.json() == missing.json()
    assert denied.content == missing.content

    volatile = {"date", "server", "content-length"}
    assert {k.lower(): v for k, v in denied.headers.items() if k.lower() not in volatile} == {
        k.lower(): v for k, v in missing.headers.items() if k.lower() not in volatile
    }


def test_denial_body_leaks_no_reason(client: TestClient) -> None:
    body = client.get("/whoami", headers={"Authorization": "Bearer wrong"}).text.lower()
    for leak in ("expired", "signature", "tenant", "organization", "forbidden", "unauthor"):
        assert leak not in body, f"denial body leaked {leak!r}"


# --- explicit propagation: no ambient state ----------------------------------


def test_context_module_exposes_no_ambient_accessor() -> None:
    """The leak this design exists to prevent is a global 'current context'."""
    import auth.context as ctx_module

    banned = [
        n
        for n in dir(ctx_module)
        if n in {"current_context", "get_current_context", "CONTEXT", "_context_var"}
    ]
    assert not banned, f"ambient context accessor(s) reintroduced: {banned}"
    assert "contextvars" not in ctx_module.__dict__


def test_job_payload_round_trip() -> None:
    ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)
    assert RequestContext.from_job_payload(ctx.to_job_payload()) == ctx


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"_journeylab_context": None},
        {"_journeylab_context": {"v": 999, "actor_id": str(USER_A), "organization_id": str(ORG_A)}},
        {"_journeylab_context": {"v": 1, "actor_id": "not-a-uuid", "organization_id": str(ORG_A)}},
        {"_journeylab_context": {"v": 1, "organization_id": str(ORG_A)}},
    ],
)
def test_job_without_valid_context_fails_closed(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        RequestContext.from_job_payload(payload)


def test_context_does_not_leak_into_a_spawned_task() -> None:
    """A task started during a request must not be able to discover the tenant."""

    async def scenario() -> None:
        ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)

        async def background_without_context() -> str:
            import auth.context as m

            return str([n for n in dir(m) if "current" in n.lower()])

        found = await asyncio.create_task(background_without_context())
        assert found == "[]"
        # The only way the task could obtain context is by being handed it.
        assert RequestContext.from_job_payload(ctx.to_job_payload()) == ctx

    asyncio.run(scenario())


def test_context_str_redacts_identifiers() -> None:
    ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)
    assert str(ORG_A) not in f"{ctx}"
    assert str(USER_A) not in f"{ctx}"


# --- event envelopes ---------------------------------------------------------


def test_envelope_is_stamped_without_mutation() -> None:
    ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)
    original = {"type": "trip_created"}
    stamped = stamp_envelope(original, ctx)

    assert stamped["tenant_id"] == str(ORG_A)
    assert stamped["actor_id"] == str(USER_A)
    assert original == {"type": "trip_created"}, "stamp_envelope mutated its input"


def test_envelope_refuses_conflicting_tenant() -> None:
    ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)
    with pytest.raises(ValueError):
        stamp_envelope({"type": "x", "tenant_id": str(ORG_B)}, ctx)


# --- TST-SEC-001: context actually reaches the database session --------------

# Default matches .env.example. Dev-only credentials, and the port is bound to
# 127.0.0.1 in docker-compose.dev.yml.


async def _ensure_seed() -> None:
    """Create exactly the rows these assertions expect.

    BUG-024. These tests asserted `count(*) == 1` against seed data that
    `tests/security/test_tenant_isolation.sh` creates as a side effect. They passed
    on any machine where R7 had ever been run and failed on a clean database — so
    they were **order-dependent on another suite**, and nothing said so.

    That went unnoticed for six steps because the tests never ran anywhere clean:
    CI skipped them (`BUG-023`). The first CI-mirror run with a real database found
    all three immediately, which is the whole argument for STEP-001.07.

    Idempotent, and it sets the counts rather than adding to them — two runs must
    leave exactly one membership per organization, or the assertion becomes a test
    of how many times the suite has been run.
    """
    import psycopg

    async with await psycopg.AsyncConnection.connect(DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES "
                "(%s,'tenant-a','Tenant A'), (%s,'tenant-b','Tenant B') "
                "ON CONFLICT (id) DO NOTHING",
                (str(ORG_A), str(ORG_B)),
            )
            await cur.execute(
                "INSERT INTO users (id, email) VALUES (%s,'a@example.test'), (%s,'b@example.test') "
                "ON CONFLICT (id) DO NOTHING",
                (str(USER_A), str(USER_B)),
            )
            await cur.execute(
                "DELETE FROM memberships WHERE organization_id IN (%s, %s)",
                (str(ORG_A), str(ORG_B)),
            )
            await cur.execute(
                "INSERT INTO memberships (organization_id, user_id, role_key) VALUES "
                "(%s,%s,'trip_owner'), (%s,%s,'trip_owner')",
                (str(ORG_A), str(USER_A), str(ORG_B), str(USER_B)),
            )
        await conn.commit()


async def _rows_visible_as(context: RequestContext) -> int:
    import psycopg

    await _ensure_seed()
    async with await psycopg.AsyncConnection.connect(DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET ROLE journeylab_app")
            await bind_tenant(cur, context)
            await cur.execute("SELECT count(*) FROM memberships")
            row = await cur.fetchone()
            return int(row[0]) if row else -1


@requires_db
def test_bound_context_reaches_the_database_session() -> None:
    """The application binding must produce the SAME isolation R7 proves in SQL."""
    assert (
        asyncio.run(_rows_visible_as(RequestContext(actor_id=USER_A, organization_id=ORG_A))) == 1
    )


@requires_db
def test_unbound_session_sees_nothing() -> None:
    """Deny-by-default: forgetting to bind must expose nothing, not everything."""
    import psycopg

    async def scenario() -> int:
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SET ROLE journeylab_app")
                await cur.execute("SELECT count(*) FROM memberships")
                row = await cur.fetchone()
                return int(row[0]) if row else -1

    assert asyncio.run(scenario()) == 0


@requires_db
def test_binding_is_injection_safe() -> None:
    """A hostile tenant value must be a bind parameter, never concatenated SQL.

    Observed behaviour, recorded rather than assumed: the hostile string reaches
    the database intact as a PARAMETER (so `DROP TABLE` is never parsed as SQL),
    and the failure surfaces later — `app_current_org()` casts the setting to uuid
    and raises `invalid input syntax for type uuid`.

    That is fail-closed but LOUD, which differs from the silent 0 rows of an unset
    context. Both deny. The distinction is deliberate and worth keeping: an unset
    context is a plausible ordering mistake, whereas a malformed one can only come
    from a bug in the binding path, and should be noisy. Carried into BR-011 §9.
    """
    import psycopg

    class Hostile:
        def __str__(self) -> str:
            return "'; DROP TABLE memberships; --"

    ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)
    object.__setattr__(ctx, "organization_id", Hostile())

    async def scenario() -> None:
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SET ROLE journeylab_app")
                await bind_tenant(cur, ctx)  # value travels as a parameter
                await cur.execute("SELECT count(*) FROM memberships")

    with pytest.raises(psycopg.errors.InvalidTextRepresentation):
        asyncio.run(scenario())

    # The decisive assertion: the table was never dropped, and isolation still holds.
    assert (
        asyncio.run(_rows_visible_as(RequestContext(actor_id=USER_A, organization_id=ORG_A))) == 1
    )


@requires_db
def test_binding_does_not_survive_the_transaction() -> None:
    """The pooled-connection leak, at the application binding layer.

    Added because mutation testing found this hole: changing `set_config`'s
    is_local argument from true to false — making the tenant SESSION-wide instead
    of transaction-scoped — passed the entire suite. A pooled connection would then
    carry one tenant's context into the next request that borrowed it.

    STEP-002.01 proves this property for raw SQL. That did not cover `bind_tenant`,
    which is the function application code actually calls.
    """
    import psycopg

    async def scenario() -> tuple[int, int]:
        await _ensure_seed()
        ctx = RequestContext(actor_id=USER_A, organization_id=ORG_A)
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SET ROLE journeylab_app")
                await bind_tenant(cur, ctx)
                await cur.execute("SELECT count(*) FROM memberships")
                row = await cur.fetchone()
                bound = int(row[0]) if row else -1
            await conn.commit()  # the connection goes back to the pool here

            async with conn.cursor() as cur:  # borrowed again, no bind this time
                await cur.execute("SELECT count(*) FROM memberships")
                row = await cur.fetchone()
                reused = int(row[0]) if row else -1
        return bound, reused

    bound, reused = asyncio.run(scenario())
    assert bound == 1, "binding did not take effect inside the transaction"
    assert reused == 0, "tenant context survived COMMIT — a pooled connection would leak it"
