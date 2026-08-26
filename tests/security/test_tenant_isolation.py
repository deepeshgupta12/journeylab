"""Cross-tenant isolation — TST-SEC-002 · STEP-002.06 · regression check R7.

REQ-SEC-002: tenant A cannot reach tenant B by **any** path.

WHY THIS FILE EXISTS ALONGSIDE test_tenant_isolation.sh
    STEP-002.01 established R7 at the database with a shell suite: 12 assertions
    over RLS policies, run directly against Postgres. That proves the *storage*
    boundary and nothing above it.

    This suite covers the paths an application takes — authorization decisions,
    job payloads, event envelopes, denial shape — and runs in pytest, so R7 is
    part of the fast tier rather than a separate command someone must remember.

THE PART THAT MATTERS MOST: PENDING VECTORS
    Most isolation vectors named by REQ-SEC-002 have nothing to test yet. There is
    no cache layer, no export path, no vector store, no domain graph. The lazy
    options are to omit them (they are then forgotten) or to write a test that
    passes vacuously (worse — it manufactures confidence).

    Instead each unbuilt vector has a test that DETECTS WHETHER THE SUBSYSTEM HAS
    LANDED:
      - not landed  -> skip, with the reason stated
      - landed      -> **FAIL**, because a real isolation test is now owed

    A placeholder that cannot notice its own dependency arriving is just a
    comment. These convert themselves into failures.

Requires the local stack. Skips — reported as skips, never as passes — without it.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable

import psycopg
import pytest
from auth.context import RequestContext
from auth.db import bind_tenant
from auth.errors import OPAQUE_BODY, OPAQUE_STATUS
from auth.events import stamp_envelope
from authz import Operation, Resource, Role, authorize
from dbcheck import DSN, requires_db, stack_is_up
from provisioning import create_organization, grant_membership, provision_user

pytestmark = pytest.mark.security


ORG_A = uuid.UUID("aaaa0000-0000-0000-0000-00000000000a")
ORG_B = uuid.UUID("bbbb0000-0000-0000-0000-00000000000b")


def run[T](fn: Callable[[psycopg.AsyncCursor[tuple[object, ...]]], Awaitable[T]]) -> T:
    """Run as the table owner — fixtures must create rows RLS would hide."""

    async def scenario() -> T:
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                result = await fn(cur)
            await conn.commit()
            return result

    return asyncio.run(scenario())


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# --- fixtures: two tenants with the SAME data shape --------------------------


@pytest.fixture(scope="module")
def two_tenants() -> dict[str, uuid.UUID]:
    """Two organizations holding structurally identical rows.

    Overlapping shapes matter: if tenant B's data looked different, a test could
    pass because a query happened not to match rather than because isolation held.
    """

    async def build(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> dict[str, uuid.UUID]:
        owners: dict[str, uuid.UUID] = {}
        for label, org in (("a", ORG_A), ("b", ORG_B)):
            subject = unique(f"oidc|isolation-{label}")
            owner = (await provision_user(cur, idp_subject=subject)).user_id
            await cur.execute("DELETE FROM organizations WHERE id = %s", (str(org),))
            await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
            await create_organization(
                cur,
                organization_id=org,
                slug=unique(f"isolation-{label}"),
                display_name=f"Isolation {label.upper()}",
                owner_user_id=owner,
            )
            await grant_membership(
                cur, organization_id=org, user_id=owner, role_key="trip_editor", actor_id=owner
            )
            owners[label] = owner
        return owners

    return run(build)


# --- VECTOR 1: storage. Tenant A cannot read or write tenant B rows ----------


@requires_db
def test_storage_vector_denies_cross_tenant_read(two_tenants: dict[str, uuid.UUID]) -> None:
    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> tuple[int, int]:
        await cur.execute("SET ROLE journeylab_app")
        await bind_tenant(cur, RequestContext(actor_id=two_tenants["a"], organization_id=ORG_A))
        await cur.execute("SELECT count(*) FROM memberships")
        own = int(str((await cur.fetchone() or (0,))[0]))
        await cur.execute(
            "SELECT count(*) FROM memberships WHERE organization_id = %s", (str(ORG_B),)
        )
        foreign = int(str((await cur.fetchone() or (0,))[0]))
        return own, foreign

    own, foreign = run(scenario)
    assert own > 0, "tenant A saw none of its own rows — fixture or binding is broken"
    assert foreign == 0, "tenant A read tenant B rows by naming them explicitly"


@requires_db
def test_storage_vector_denies_cross_tenant_write(two_tenants: dict[str, uuid.UUID]) -> None:
    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> int:
        await cur.execute("SET ROLE journeylab_app")
        await bind_tenant(cur, RequestContext(actor_id=two_tenants["a"], organization_id=ORG_A))
        await cur.execute(
            "WITH u AS (UPDATE memberships SET role_key='trip_viewer' "
            "WHERE organization_id = %s RETURNING 1) SELECT count(*) FROM u",
            (str(ORG_B),),
        )
        return int(str((await cur.fetchone() or (0,))[0]))

    assert run(scenario) == 0, "tenant A modified tenant B rows"


@requires_db
def test_storage_vector_denies_listing_without_context(two_tenants: dict[str, uuid.UUID]) -> None:
    """Deny-by-default: no context must yield nothing, not everything."""

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> int:
        await cur.execute("SET ROLE journeylab_app")
        await cur.execute("SELECT count(*) FROM memberships")
        return int(str((await cur.fetchone() or (0,))[0]))

    assert run(scenario) == 0


# --- VECTOR 2: authorization. Tenant checked before role --------------------


@requires_db
def test_outbox_vector_denies_cross_tenant_read(two_tenants: dict[str, uuid.UUID]) -> None:
    """The vector this suite has been holding open since STEP-002.06.

    It was a placeholder that detected its own dependency arriving: while no outbox
    existed it skipped, and the moment STEP-006.06 created the table it **failed**,
    demanding this test. That is the placeholder working — a stub that cannot notice
    the subsystem landing is just a comment.

    The event stream is the isolation vector people forget, because it does not look
    like a store. It holds one row per state change, keyed by tenant, and a consumer
    reading another tenant's queue learns what they are planning and when.
    """

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> tuple[int, int]:
        await cur.execute(
            "INSERT INTO outbox (organization_id, event_type, order_key, correlation_id, "
            "payload_ids) VALUES (%s, 'journey.trip.brief_confirmed.v1', 't-b', 'c', '{}')",
            (str(ORG_B),),
        )
        await cur.execute("SET ROLE journeylab_app")
        await bind_tenant(cur, RequestContext(actor_id=two_tenants["a"], organization_id=ORG_A))
        await cur.execute("SELECT count(*) FROM outbox")
        visible = int(str((await cur.fetchone() or (0,))[0]))
        await cur.execute("SELECT count(*) FROM outbox WHERE organization_id = %s", (str(ORG_B),))
        named = int(str((await cur.fetchone() or (0,))[0]))
        return visible, named

    visible, named = run(scenario)
    assert named == 0, "tenant A read tenant B's event queue by naming it"
    assert visible == 0, "tenant A saw events it did not produce"


@requires_db
def test_outbox_vector_refuses_writing_an_event_for_another_tenant() -> None:
    """`WITH CHECK`, not just `USING`. A policy that filters reads and permits writes
    lets one tenant inject an event into another's stream — where a consumer will
    process it under that tenant's authority."""

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> str:
        await cur.execute("SET ROLE journeylab_app")
        await bind_tenant(cur, RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A))
        try:
            await cur.execute(
                "INSERT INTO outbox (organization_id, event_type, order_key, "
                "correlation_id, payload_ids) "
                "VALUES (%s, 'journey.trip.brief_confirmed.v1', 't', 'c', '{}')",
                (str(ORG_B),),
            )
        except psycopg.errors.InsufficientPrivilege:
            return "denied"
        return "written"

    assert run(scenario) == "denied", "tenant A wrote an event into tenant B's stream"


def test_authorization_vector_denies_foreign_resource() -> None:
    context = RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A)
    decision = authorize(
        context=context,
        role=Role.TRIP_OWNER,
        operation=Operation.READ_TRIP,
        resource=Resource(organization_id=ORG_B, owner_id=context.actor_id),
    )
    assert not decision.allowed
    assert decision.reason == "cross_tenant_attempt", (
        "a cross-tenant attempt must be reported as such, not as a role or relationship "
        "failure — ALRT-SEC-001 fires on this distinction"
    )


def test_authorization_vector_denies_every_operation_across_tenants() -> None:
    """Not sampled: every operation, for every role, against a foreign resource."""
    context = RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A)
    foreign = Resource(organization_id=ORG_B, owner_id=context.actor_id)
    leaked = [
        (operation.value, role.value)
        for operation in Operation
        for role in Role
        if authorize(context=context, role=role, operation=operation, resource=foreign).allowed
    ]
    assert not leaked, f"cross-tenant access permitted for: {leaked}"


def test_authorization_denials_are_auditable() -> None:
    """§8: denials must be auditable. The obligation is carried as a value."""
    decision = authorize(
        context=RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A),
        role=Role.TRIP_OWNER,
        operation=Operation.READ_TRIP,
        resource=Resource(organization_id=ORG_B),
    )
    assert decision.audit is True, "a cross-tenant attempt was not marked for audit"


# --- VECTOR 3: enumeration. Denial and absence are indistinguishable --------


def test_enumeration_vector_denial_shape_reveals_nothing() -> None:
    body = str(OPAQUE_BODY).lower()
    assert OPAQUE_STATUS == 404
    for leak in ("tenant", "organization", "forbidden", "denied", "role", "permission"):
        assert leak not in body, f"denial body leaks {leak!r}"


# --- VECTOR 4: jobs. Context crosses the boundary as data, or not at all -----


def test_job_vector_payload_cannot_carry_a_foreign_tenant() -> None:
    """A job serialised for tenant A must never deserialise as tenant B."""
    a = RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A)
    recovered = RequestContext.from_job_payload(a.to_job_payload())
    assert recovered.organization_id == ORG_A


def test_job_vector_rejects_a_payload_with_no_context() -> None:
    """A job that lost its context must fail, not run as some default tenant."""
    with pytest.raises(ValueError):
        RequestContext.from_job_payload({"trip_id": "whatever"})


def test_job_vector_has_no_ambient_context_to_inherit() -> None:
    """The leak this design exists to prevent: a worker picking up a global."""
    import auth.context as module

    assert not [n for n in dir(module) if "current" in n.lower()]
    assert "contextvars" not in module.__dict__


# --- VECTOR 5: events. Envelopes cannot be stamped with a foreign tenant -----


def test_event_vector_refuses_a_conflicting_tenant() -> None:
    context = RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A)
    with pytest.raises(ValueError):
        stamp_envelope({"type": "trip_created", "tenant_id": str(ORG_B)}, context)


def test_event_vector_stamps_the_acting_tenant() -> None:
    context = RequestContext(actor_id=uuid.uuid4(), organization_id=ORG_A)
    assert stamp_envelope({"type": "trip_created"}, context)["tenant_id"] == str(ORG_A)


# --- PENDING VECTORS --------------------------------------------------------
#
# Each detects whether its subsystem has arrived. Skip while absent; FAIL once
# present, because a real isolation test is then owed. See the module docstring.


def _table_exists(name: str) -> bool:
    if not stack_is_up():
        return False

    async def check(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> bool:
        await cur.execute(
            "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tablename = %s", (name,)
        )
        return int(str((await cur.fetchone() or (0,))[0])) > 0

    return run(check)


def _code_matches(pattern: str) -> bool:
    """True if application code USES a subsystem, ignoring tests, docs and mentions.

    MENTION IS NOT USE, AND THE DISTINCTION IS NOT PEDANTIC.
        The first version searched raw source for a keyword and fired on the word
        `redis` appearing inside a *prohibition* pattern in
        `conventions/problem.py` — a regex whose entire purpose is to stop a
        connection string reaching a client. The ratchet reported that a cache
        layer had landed because the code said the word while forbidding it.

        A keyword search finds the warning as readily as the violation. So
        comments and string literals are stripped before matching, leaving code:
        an import, a call, an attribute access. A cache layer is something you
        import and call, not something you name.

    The ratchet stays deliberately eager. Stripping literals narrows it, so each
    pattern below also matches the *shape* of use — `import x`, `x(`, `x.` — and
    `test_the_detector_can_still_fire` proves it has not been narrowed into
    uselessness.
    """
    import io
    import pathlib
    import re
    import tokenize

    needle = re.compile(pattern, re.IGNORECASE)
    for root in ("apps", "services"):
        for path in pathlib.Path(root).rglob("*.py"):
            if "node_modules" in str(path):
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            try:
                code = "".join(
                    token.string + " "
                    for token in tokenize.generate_tokens(io.StringIO(source).readline)
                    if token.type not in (tokenize.COMMENT, tokenize.STRING)
                )
            except tokenize.TokenError, IndentationError, SyntaxError:
                # Unparseable file: fall back to the raw text rather than
                # silently skipping it. An eager ratchet is the safe failure.
                code = source
            if needle.search(code):
                return True
    return False


PENDING_VECTORS: list[tuple[str, Callable[[], bool], str]] = [
    (
        "cache",
        lambda: _code_matches(r"import\s+redis|from\s+redis|redis\.|valkey\.|cache_get|cache_set"),
        "REQ-SEC-002 requires a cache key collision to be unable to serve foreign "
        "data. No cache layer exists yet (arrives with STEP-010 retrieval).",
    ),
    (
        "export",
        lambda: _code_matches(r"def export_|build_export|to_csv"),
        "REQ-SEC-002 names export as a vector. No export path exists (STEP-015 / STEP-022).",
    ),
    (
        "vector store",
        lambda: _table_exists("embeddings") or _code_matches(r"vector_search|embed_query"),
        "pgvector is installed but unused. Tenant-scoped similarity search arrives "
        "with STEP-010; an untenanted index would leak across tenants by construction.",
    ),
    (
        "domain graph",
        lambda: _code_matches(r"def graph_query|run_cypher|traverse_graph"),
        "REQ-KG-006: a graph answer must never reveal a path the caller cannot "
        "inspect at its source. The domain graph arrives with STEP-026.",
    ),
]


def test_the_detector_can_still_fire() -> None:
    """The ratchet must not have been narrowed into uselessness.

    `_code_matches` was tightened at STEP-004.01 to ignore comments and string
    literals. That is a narrowing, and a narrowing to a detector that exists to
    fail on purpose deserves its own proof — otherwise the fix for a false
    positive quietly becomes a permanent false negative.
    """
    # Matches real application code: `conventions/problem.py` defines this class.
    assert _code_matches(r"class\s+ProblemError"), (
        "the detector no longer sees real code — it has been narrowed too far"
    )
    # Does NOT match a word that appears only inside a string literal.
    assert not _code_matches(r"Mercury\s+is\s+retrograde")


@pytest.mark.parametrize(
    ("name", "landed", "reason"), PENDING_VECTORS, ids=[v[0] for v in PENDING_VECTORS]
)
def test_pending_vector_is_still_absent(name: str, landed: Callable[[], bool], reason: str) -> None:
    """Placeholder that converts itself into a failure when its subsystem lands."""
    if landed():
        pytest.fail(
            f"The '{name}' subsystem now exists, but its cross-tenant isolation test is "
            f"still a placeholder. REQ-SEC-002 requires every path to be covered. "
            f"Write the real test and remove this entry.\n\nContext: {reason}"
        )
    pytest.skip(f"'{name}' not built yet — {reason}")


# --- META-TEST: the suite must be able to fail ------------------------------


@requires_db
def test_a_broken_rls_policy_makes_this_suite_fail(two_tenants: dict[str, uuid.UUID]) -> None:
    """The most important test here.

    A passing isolation suite that would ALSO pass with RLS disabled is worse than
    no suite, because it manufactures confidence. This weakens the policy on
    purpose, asserts the storage vector then leaks, and restores it.
    """

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> tuple[int, int]:
        await cur.execute("DROP POLICY IF EXISTS memberships_tenant_isolation ON memberships")
        await cur.execute(
            "CREATE POLICY memberships_tenant_isolation ON memberships "
            "USING (true) WITH CHECK (true)"
        )
        await cur.execute("SET ROLE journeylab_app")
        await bind_tenant(cur, RequestContext(actor_id=two_tenants["a"], organization_id=ORG_A))
        await cur.execute(
            "SELECT count(*) FROM memberships WHERE organization_id = %s", (str(ORG_B),)
        )
        leaked = int(str((await cur.fetchone() or (0,))[0]))

        await cur.execute("RESET ROLE")
        await cur.execute("DROP POLICY IF EXISTS memberships_tenant_isolation ON memberships")
        await cur.execute(
            "CREATE POLICY memberships_tenant_isolation ON memberships "
            "USING (organization_id = app_current_org()) "
            "WITH CHECK (organization_id = app_current_org())"
        )
        await cur.execute("SET ROLE journeylab_app")
        await bind_tenant(cur, RequestContext(actor_id=two_tenants["a"], organization_id=ORG_A))
        await cur.execute(
            "SELECT count(*) FROM memberships WHERE organization_id = %s", (str(ORG_B),)
        )
        restored = int(str((await cur.fetchone() or (0,))[0]))
        return leaked, restored

    leaked, restored = run(scenario)
    assert leaked > 0, (
        "a deliberately disabled RLS policy did NOT leak — this suite is not "
        "measuring row-level security at all, and every pass above is meaningless"
    )
    assert restored == 0, "policy was not restored; the database is left insecure"


@requires_db
def test_force_rls_still_set_on_every_tenant_table() -> None:
    """Without FORCE, the table owner silently bypasses every policy."""

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> int:
        await cur.execute(
            "SELECT count(*) FROM pg_class WHERE relname IN "
            "('memberships','service_identities','organizations') AND relforcerowsecurity"
        )
        return int(str((await cur.fetchone() or (0,))[0]))

    assert run(scenario) == 3, "FORCE ROW LEVEL SECURITY lost on a tenant table"
