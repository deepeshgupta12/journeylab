"""Audit emission and runtime flags — TST-SEC-007, TST-PLAT-012 · STEP-002.07."""

import asyncio
import os
import socket
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from audit import AuditEvent, AuditWriteError, emit, from_decision
from auth.context import RequestContext
from auth.db import bind_tenant
from flags import Evaluation, Flag, evaluate, evaluate_bool
from provisioning import create_organization, provision_user
from redaction import MASK, RedactionError, redact

DSN = os.environ.get(
    "JOURNEYLAB_TEST_DSN",
    "postgresql://journeylab:journeylab_dev_only@127.0.0.1:5700/journeylab",
)
ORG = uuid.UUID("cccc0000-0000-0000-0000-00000000000c")


def _stack_up() -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", 5700)) == 0


requires_db = pytest.mark.skipif(not _stack_up(), reason="local stack not running (pnpm dev)")


def run[T](fn: Callable[[psycopg.AsyncCursor[tuple[object, ...]]], Awaitable[T]]) -> T:
    async def scenario() -> T:
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                result = await fn(cur)
            await conn.commit()
            return result

    return asyncio.run(scenario())


def now() -> datetime:
    return datetime.now(UTC)


# --- REQ-SEC-007: redaction happens at emission ------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "hunter2"},
        {"api_key": "abc123"},
        {"authorization": "Bearer xyz"},
        {"session_token": "s3cret"},
        {"nested": {"client_secret": "shh"}},
        {"list": [{"private_key": "k"}]},
    ],
)
def test_sensitive_keys_are_masked(payload: dict[str, object]) -> None:
    assert MASK in str(redact(payload))
    assert "hunter2" not in str(redact(payload))


@pytest.mark.parametrize(
    "value",
    [
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig",  # JWT under an innocuous key
        "Bearer abcdefghijklmnop",
        "sk-abcdefghijklmnopqrstuvwx",
        "-----BEGIN RSA PRIVATE KEY-----",
        "a" * 40,  # long hex
    ],
)
def test_secret_shaped_values_are_caught_whatever_the_key(value: str) -> None:
    """The key name is innocuous; the value is not. This is the important case."""
    assert redact({"note": value})["note"] == MASK


def test_email_is_reduced_to_its_domain() -> None:
    """PII out, operational signal kept."""
    result = redact({"subject": "user traveller@example.test signed in"})["subject"]
    assert "traveller" not in str(result)
    assert "example.test" in str(result)


def test_lists_of_secrets_are_masked_element_wise() -> None:
    assert redact({"note": ["eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig"]})["note"] == [MASK]


def test_a_secret_in_an_unhandled_type_blocks_emission() -> None:
    """The fail-closed branch, and it was nearly decorative.

    `_redact_value` understands dict, list and str. A tuple passed through
    completely untouched — the private key below was returned verbatim — and the
    safety sweep did not traverse tuples either, so nothing noticed.

    Now the sweep checks the string form of any type it does not understand, so an
    unmaskable value refuses the write instead of being stored in an append-only
    table it could never be deleted from.
    """
    with pytest.raises(RedactionError, match="append-only"):
        redact({"leaked": ("-----BEGIN RSA PRIVATE KEY-----",)})


def test_ordinary_unhandled_types_still_pass() -> None:
    """The sweep must not refuse everything it does not recognise."""
    assert redact({"ids": (1, 2, 3)}) == {"ids": (1, 2, 3)}


def test_non_string_values_survive_redaction() -> None:
    payload = {"count": 3, "ok": True, "ratio": 1.5, "missing": None}
    assert redact(payload) == payload


# --- REQ-SEC-007: append-only, enforced by the database ---------------------


@requires_db
def test_audit_events_can_be_written_and_read() -> None:
    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> tuple[uuid.UUID, int]:
        owner = (
            await provision_user(cur, idp_subject=f"oidc|audit-{uuid.uuid4().hex[:8]}")
        ).user_id
        await cur.execute("DELETE FROM organizations WHERE id = %s", (str(ORG),))
        await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=ORG))
        await create_organization(
            cur,
            organization_id=ORG,
            slug=f"audit-{uuid.uuid4().hex[:8]}",
            display_name="Audit",
            owner_user_id=owner,
        )
        event_id = await emit(
            cur,
            AuditEvent(
                action="membership.revoked",
                subject=f"user:{owner}",
                outcome="denied",
                occurred_at=now(),
                organization_id=ORG,
                actor_id=owner,
                payload={"reason": "cross_tenant_attempt"},
            ),
        )
        await cur.execute("SELECT count(*) FROM audit_events WHERE id = %s", (str(event_id),))
        return event_id, int(str((await cur.fetchone() or (0,))[0]))

    event_id, found = run(scenario)
    assert found == 1, f"audit event {event_id} was not written"


@requires_db
def test_application_role_cannot_update_or_delete_audit_events() -> None:
    """Append-only is a PRIVILEGE, not a convention. Code cannot talk around it."""

    async def attempt(cur: psycopg.AsyncCursor[tuple[object, ...]], sql: str) -> str:
        try:
            await cur.execute("SET ROLE journeylab_app")
            await cur.execute(sql)
        except Exception as exc:
            return type(exc).__name__ + ":" + str(exc)[:60]
        return "NOT DENIED"

    def attempting(sql: str) -> Callable[[psycopg.AsyncCursor[tuple[object, ...]]], Awaitable[str]]:
        async def inner(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> str:
            return await attempt(cur, sql)

        return inner

    for sql in (
        "UPDATE audit_events SET outcome = 'allowed'",
        "DELETE FROM audit_events",
        "TRUNCATE audit_events",
    ):
        result = run(attempting(sql))
        assert "NOT DENIED" not in result, f"journeylab_app was allowed to run: {sql}"
        assert "permission denied" in result.lower(), f"{sql} failed for the wrong reason: {result}"


@requires_db
def test_audit_write_failure_is_raised_not_swallowed() -> None:
    """§8: a silent audit failure is a compliance gap."""

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> str:
        try:
            await emit(
                cur,
                AuditEvent(
                    action="not a valid action shape",  # violates the CHECK constraint
                    subject="x",
                    outcome="allowed",
                    occurred_at=now(),
                ),
            )
        except AuditWriteError as exc:
            return str(exc)
        return "NO ERROR RAISED"

    assert "not a valid action shape" in run(scenario)


def test_naive_timestamps_are_rejected() -> None:
    """Ordering is most of what an investigation depends on."""
    with pytest.raises(ValueError, match="timezone-aware"):
        AuditEvent(
            action="a.b",
            subject="x",
            outcome="allowed",
            occurred_at=datetime(2026, 1, 1),  # noqa: DTZ001
        )


def test_denial_reason_belongs_in_the_audit_event_only() -> None:
    """The reason is withheld from the response and recorded here."""
    event = from_decision(
        action="trip.read",
        subject="trip:1",
        allowed=False,
        organization_id=ORG,
        actor_id=uuid.uuid4(),
        reason="cross_tenant_attempt",
    )
    assert event.outcome == "denied"
    assert event.payload == {"reason": "cross_tenant_attempt"}


# --- REQ-PLAT-012: flags ----------------------------------------------------


def test_flag_requires_a_conservative_value() -> None:
    """No default: which direction is safe differs per flag."""
    import inspect

    parameters = inspect.signature(Flag).parameters
    assert parameters["conservative"].default is inspect.Parameter.empty


def test_flag_key_cannot_be_blank() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        Flag(key="  ", conservative=False)


@requires_db
def test_flag_change_alters_behaviour_without_restart() -> None:
    """TST-PLAT-012: same process, same connection, new value."""
    key = f"test.flag.{uuid.uuid4().hex[:8]}"
    flag = Flag(key=key, conservative=False)

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> tuple[bool, bool, bool]:
        before = await evaluate_bool(cur, flag)
        await cur.execute(
            "INSERT INTO feature_flags (key, organization_id, value) VALUES (%s, NULL, 'true'::jsonb)",
            (key,),
        )
        after = await evaluate_bool(cur, flag)
        await cur.execute("UPDATE feature_flags SET value = 'false'::jsonb WHERE key = %s", (key,))
        reverted = await evaluate_bool(cur, flag)
        await cur.execute("DELETE FROM feature_flags WHERE key = %s", (key,))
        return before, after, reverted

    before, after, reverted = run(scenario)
    assert before is False, "an unset flag should be conservative"
    assert after is True, "flag change did not take effect without a restart"
    assert reverted is False


@requires_db
def test_tenant_override_beats_the_global_default() -> None:
    key = f"test.flag.{uuid.uuid4().hex[:8]}"
    flag = Flag(key=key, conservative=False)

    async def scenario(
        cur: psycopg.AsyncCursor[tuple[object, ...]],
    ) -> tuple[Evaluation, Evaluation]:
        await cur.execute(
            "INSERT INTO feature_flags (key, organization_id, value) VALUES (%s, NULL, 'false'::jsonb)",
            (key,),
        )
        await cur.execute(
            "INSERT INTO feature_flags (key, organization_id, value) VALUES (%s, %s, 'true'::jsonb)",
            (key, str(ORG)),
        )
        global_value = await evaluate(cur, flag)
        tenant_value = await evaluate(cur, flag, organization_id=ORG)
        await cur.execute("DELETE FROM feature_flags WHERE key = %s", (key,))
        return global_value, tenant_value

    global_value, tenant_value = run(scenario)
    assert global_value.source == "global"
    assert tenant_value.source == "tenant"
    assert tenant_value.value is True


def test_unreachable_flag_store_yields_the_conservative_value() -> None:
    """The trap named in the sub-step: an outage must not ENABLE anything."""

    class BrokenCursor:
        async def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
            raise ConnectionError("flag store unreachable")

        async def fetchone(self) -> tuple[object, ...] | None:
            return None

    async def scenario() -> tuple[Evaluation, Evaluation]:
        off = await evaluate(BrokenCursor(), Flag(key="new_ui", conservative=False))
        on = await evaluate(BrokenCursor(), Flag(key="require_consent", conservative=True))
        return off, on

    off, on = asyncio.run(scenario())
    assert off.value is False, "an outage ENABLED a feature — conservative is backwards"
    assert on.value is True, "an outage DISABLED a consent gate — conservative is backwards"
    assert off.source == "conservative" and not off.resolved


def test_a_malformed_value_is_not_interpreted_generously() -> None:
    """`{"enabled": true}` is not `true`."""

    class WeirdCursor:
        async def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
            return None

        async def fetchone(self) -> tuple[object, ...] | None:
            return ({"enabled": True}, None)

    async def scenario() -> bool:
        return await evaluate_bool(WeirdCursor(), Flag(key="x", conservative=False))

    assert asyncio.run(scenario()) is False


@requires_db
def test_application_role_cannot_change_flags() -> None:
    """Flag changes are an administrative act (STEP-021), not a request-time one."""

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> str:
        try:
            await cur.execute("SET ROLE journeylab_app")
            await cur.execute("INSERT INTO feature_flags (key, value) VALUES ('x', 'true'::jsonb)")
        except Exception as exc:
            return str(exc)[:80]
        return "NOT DENIED"

    result = run(scenario)
    assert "permission denied" in result.lower(), f"app role could write a flag: {result}"


@requires_db
def test_future_dated_events_are_rejected() -> None:
    """A clock-skewed emitter would sort above every real event forever."""

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> str:
        try:
            await emit(
                cur,
                AuditEvent(
                    action="test.emitted",
                    subject="x",
                    outcome="allowed",
                    occurred_at=now() + timedelta(days=400),
                ),
            )
        except AuditWriteError as exc:
            return str(exc)
        return "NOT REJECTED"

    assert "NOT REJECTED" not in run(scenario)
