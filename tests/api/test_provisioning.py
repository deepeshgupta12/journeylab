"""Identity provisioning — TST-SEC-003, TST-TRIP-005 · STEP-002.04.

These are integration tests against the real database, because every guarantee in
this sub-step is a database guarantee: idempotency comes from a unique index,
isolation from RLS, and "exactly one copy" from a conflict clause. A fake cursor
would test the SQL I meant to write rather than the SQL that runs.

They SKIP when the local stack is down. A skip is reported as a skip.
"""

import asyncio
import os
import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from auth.context import RequestContext
from auth.db import bind_tenant
from provisioning import (
    CREDENTIAL_COLUMN_PATTERN,
    AuditRecord,
    MigrationReport,
    ProvisionedUser,
    active_role_keys,
    create_guest_user,
    create_organization,
    grant_membership,
    migrate_guest_to_account,
    provision_user,
    register_service_identity,
    revoke_membership,
    revoke_service_identity,
)

DSN = os.environ.get(
    "JOURNEYLAB_TEST_DSN",
    "postgresql://journeylab:journeylab_dev_only@127.0.0.1:5700/journeylab",
)


def _stack_up() -> bool:
    import socket

    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", 5700)) == 0


requires_db = pytest.mark.skipif(not _stack_up(), reason="local stack not running (pnpm dev)")


def run_as_owner[T](
    fn: Callable[[psycopg.AsyncCursor[tuple[object, ...]]], Awaitable[T]],
) -> T:
    """Run against the table owner — provisioning writes rows RLS would hide.

    Provisioning legitimately creates organizations and users that no tenant
    context can yet see. It therefore runs as the owner rather than as
    `journeylab_app`, and `test_provisioning_does_not_weaken_rls` proves this
    privilege does not leak into the application role.
    """

    async def scenario() -> T:
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                result = await fn(cur)
            await conn.commit()
            return result

    return asyncio.run(scenario())


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


async def make_user(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> uuid.UUID:
    """Create a real, identifiable user.

    Uses `provision_user` rather than a raw INSERT. Migration 001 carries a check
    constraint — `users_identifiable_unless_guest` — requiring a non-guest to have
    an idp_subject or an email, and hand-rolled fixtures violated it. Going through
    the production path means the fixture cannot drift from the schema's rules.
    """
    subject = unique("oidc|fixture")
    result = await provision_user(cur, idp_subject=subject, email=f"{subject}@example.test")
    return result.user_id


# --- REQ-SEC-003: no static long-lived credentials ---------------------------


@requires_db
def test_identity_schema_stores_no_credentials() -> None:
    """The strongest form of "no static keys": nowhere to put one."""

    async def check(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> list[str]:
        await cur.execute(
            "SELECT table_name || '.' || column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "AND table_name IN "
            "('users','organizations','memberships','roles','service_identities')"
        )
        return [str(r[0]) for r in await cur.fetchall()]

    columns = run_as_owner(check)
    assert columns, "no identity columns found — precondition failed, not a pass"
    offenders = [c for c in columns if CREDENTIAL_COLUMN_PATTERN.search(c.split(".", 1)[1])]
    assert not offenders, f"credential-shaped columns in the identity schema: {offenders}"


def test_the_credential_scan_can_actually_fail() -> None:
    """META-TEST: the pattern must match real credential column names.

    Without this, `test_identity_schema_stores_no_credentials` passes because the
    regex matches nothing at all, which is indistinguishable from a clean schema.
    """
    for bad in ("api_key", "apikey", "client_secret", "password", "private_key", "refresh_token"):
        assert CREDENTIAL_COLUMN_PATTERN.search(bad), f"pattern missed {bad!r}"
    for good in ("role_key", "idp_subject", "workload_subject", "display_name"):
        assert not CREDENTIAL_COLUMN_PATTERN.search(good), f"pattern false-positived on {good!r}"


@requires_db
def test_service_identity_registration_accepts_no_secret() -> None:
    org = uuid.uuid4()
    name = unique("worker")

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> tuple[str, int]:
        user = await make_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=user, organization_id=org))
        await create_organization(
            cur,
            organization_id=org,
            slug=unique("org"),
            display_name="Test Org",
            owner_user_id=user,
        )
        audit = await register_service_identity(
            cur,
            organization_id=org,
            name=name,
            workload_subject="spiffe://cluster/ns/default/sa/planner",
            actor_id=user,
        )
        await cur.execute(
            "SELECT count(*) FROM service_identities WHERE organization_id=%s AND name=%s",
            (str(org), name),
        )
        row = await cur.fetchone()
        return audit.action, int(str(row[0])) if row else -1

    action, count = run_as_owner(scenario)
    assert action == "service_identity.registered"
    assert count == 1

    # The guarantee is structural: there is no parameter for a secret.
    import inspect

    params = set(inspect.signature(register_service_identity).parameters)
    assert not {p for p in params if CREDENTIAL_COLUMN_PATTERN.search(p)}


@requires_db
def test_service_identity_revocation_is_recorded() -> None:
    org = uuid.uuid4()
    name = unique("worker")

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> object:
        user = await make_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=user, organization_id=org))
        await create_organization(
            cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=user
        )
        await register_service_identity(
            cur, organization_id=org, name=name, workload_subject="wl", actor_id=user
        )
        await revoke_service_identity(cur, organization_id=org, name=name, actor_id=user)
        await cur.execute(
            "SELECT revoked_at IS NOT NULL FROM service_identities "
            "WHERE organization_id=%s AND name=%s",
            (str(org), name),
        )
        row = await cur.fetchone()
        return row[0] if row else None

    assert run_as_owner(scenario) is True


# --- idempotent user provisioning -------------------------------------------


@requires_db
def test_provisioning_is_idempotent_by_idp_subject() -> None:
    subject = unique("oidc|user")

    async def scenario(
        cur: psycopg.AsyncCursor[tuple[object, ...]],
    ) -> tuple[ProvisionedUser, ProvisionedUser, ProvisionedUser, int]:
        first = await provision_user(cur, idp_subject=subject, email=f"{subject}@example.test")
        second = await provision_user(cur, idp_subject=subject, email=f"{subject}@example.test")
        third = await provision_user(cur, idp_subject=subject)
        await cur.execute("SELECT count(*) FROM users WHERE idp_subject=%s", (subject,))
        row = await cur.fetchone()
        return first, second, third, int(str(row[0])) if row else -1

    first, second, third, count = run_as_owner(scenario)
    assert count == 1, "repeated provisioning created duplicate users"
    assert first.user_id == second.user_id == third.user_id
    assert first.created is True
    assert second.created is False, "a repeat login was reported as a first login"
    assert first.audit.action == "user.provisioned"
    assert second.audit.action == "user.reauthenticated"


@requires_db
def test_concurrent_first_logins_yield_one_user() -> None:
    """The race the unique index exists to lose safely.

    Two connections provision the same subject at the same time. Exactly one row
    must exist afterwards and both callers must receive the same id.
    """
    subject = unique("oidc|concurrent")

    async def one() -> uuid.UUID:
        async with await psycopg.AsyncConnection.connect(DSN) as conn:
            async with conn.cursor() as cur:
                result = await provision_user(cur, idp_subject=subject)
            await conn.commit()
            return result.user_id

    async def both() -> tuple[uuid.UUID, uuid.UUID]:
        a, b = await asyncio.gather(one(), one())
        return a, b

    a, b = asyncio.run(both())
    assert a == b, "concurrent first logins produced two different users"

    async def count(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> int:
        await cur.execute("SELECT count(*) FROM users WHERE idp_subject=%s", (subject,))
        row = await cur.fetchone()
        return int(str(row[0])) if row else -1

    assert run_as_owner(count) == 1


def test_blank_subject_is_rejected() -> None:
    async def scenario() -> None:
        await provision_user(_NullCursor(), idp_subject="   ")

    with pytest.raises(ValueError):
        asyncio.run(scenario())


class _NullCursor:
    """Never reached — the guard raises before any SQL runs."""

    async def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
        raise AssertionError("SQL executed despite an invalid subject")

    async def fetchone(self) -> tuple[object, ...] | None:
        return None

    async def fetchall(self) -> list[tuple[object, ...]]:
        return []


# --- memberships: grant, revoke, expiry --------------------------------------


@requires_db
def test_revocation_removes_the_role_immediately() -> None:
    org = uuid.uuid4()

    async def scenario(
        cur: psycopg.AsyncCursor[tuple[object, ...]],
    ) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
        owner, member = await make_user(cur), await make_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
        await create_organization(
            cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=owner
        )
        await grant_membership(
            cur, organization_id=org, user_id=member, role_key="trip_editor", actor_id=owner
        )
        before = await active_role_keys(cur, organization_id=org, user_id=member)
        await revoke_membership(
            cur, organization_id=org, user_id=member, role_key="trip_editor", actor_id=owner
        )
        after = await active_role_keys(cur, organization_id=org, user_id=member)
        await grant_membership(
            cur, organization_id=org, user_id=member, role_key="trip_editor", actor_id=owner
        )
        regranted = await active_role_keys(cur, organization_id=org, user_id=member)
        return before, after, regranted

    before, after, regranted = run_as_owner(scenario)
    assert before == {"trip_editor"}
    assert after == frozenset(), "revoked role was still active"
    assert regranted == {"trip_editor"}, "a revoked membership could not be reinstated"


@requires_db
def test_revoked_membership_row_is_retained_not_deleted() -> None:
    """Deleting would erase the evidence that access was once held."""
    org = uuid.uuid4()

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> int:
        owner = await make_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
        await create_organization(
            cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=owner
        )
        await revoke_membership(
            cur, organization_id=org, user_id=owner, role_key="trip_owner", actor_id=owner
        )
        await cur.execute(
            "SELECT count(*) FROM memberships WHERE organization_id=%s AND user_id=%s",
            (str(org), str(owner)),
        )
        row = await cur.fetchone()
        return int(str(row[0])) if row else -1

    assert run_as_owner(scenario) == 1


@requires_db
def test_expired_membership_is_not_active() -> None:
    org = uuid.uuid4()

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> frozenset[str]:
        owner, member = await make_user(cur), await make_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
        await create_organization(
            cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=owner
        )
        await grant_membership(
            cur,
            organization_id=org,
            user_id=member,
            role_key="trip_viewer",
            actor_id=owner,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        return await active_role_keys(cur, organization_id=org, user_id=member)

    assert run_as_owner(scenario) == frozenset()


def test_naive_expiry_is_rejected() -> None:
    async def scenario() -> None:
        await grant_membership(
            _NullCursor(),
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role_key="trip_viewer",
            actor_id=uuid.uuid4(),
            expires_at=datetime(2099, 1, 1),  # noqa: DTZ001
        )

    with pytest.raises(ValueError):
        asyncio.run(scenario())


# --- TST-TRIP-005: guest -> account migration --------------------------------


@requires_db
def test_guest_migration_moves_holdings_exactly_once() -> None:
    """Replaying the migration must not duplicate anything."""
    org_a, org_b = uuid.uuid4(), uuid.uuid4()

    async def scenario(
        cur: psycopg.AsyncCursor[tuple[object, ...]],
    ) -> tuple[MigrationReport, MigrationReport, MigrationReport, int]:
        owner = await make_user(cur)
        account = await make_user(cur)
        guest_id = await create_guest_user(cur)

        for org in (org_a, org_b):
            await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
            await create_organization(
                cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=owner
            )
            await grant_membership(
                cur, organization_id=org, user_id=guest_id, role_key="trip_owner", actor_id=owner
            )

        first = await migrate_guest_to_account(
            cur, guest_user_id=guest_id, account_user_id=account, actor_id=account
        )
        second = await migrate_guest_to_account(
            cur, guest_user_id=guest_id, account_user_id=account, actor_id=account
        )
        third = await migrate_guest_to_account(
            cur, guest_user_id=guest_id, account_user_id=account, actor_id=account
        )
        await cur.execute(
            "SELECT count(*) FROM memberships WHERE user_id=%s AND revoked_at IS NULL",
            (str(account),),
        )
        row = await cur.fetchone()
        return first, second, third, int(str(row[0])) if row else -1

    first, second, third, final = run_as_owner(scenario)

    assert first.memberships_before_guest == 2
    assert first.memberships_moved == 2
    assert not first.duplicated
    assert not first.already_migrated

    assert second.already_migrated is True, "replay did not detect an already-migrated guest"
    assert second.memberships_moved == 0
    assert third.memberships_moved == 0

    assert final == 2, f"expected exactly 2 memberships after replay, found {final}"


@requires_db
def test_migration_does_not_duplicate_a_role_the_account_already_has() -> None:
    org = uuid.uuid4()

    async def scenario(
        cur: psycopg.AsyncCursor[tuple[object, ...]],
    ) -> tuple[MigrationReport, int]:
        owner, account = await make_user(cur), await make_user(cur)
        guest_id = await create_guest_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
        await create_organization(
            cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=owner
        )
        # both guest and account already hold the same role in the same org
        for u in (guest_id, account):
            await grant_membership(
                cur, organization_id=org, user_id=u, role_key="trip_editor", actor_id=owner
            )
        report = await migrate_guest_to_account(
            cur, guest_user_id=guest_id, account_user_id=account, actor_id=account
        )
        await cur.execute(
            "SELECT count(*) FROM memberships "
            "WHERE user_id=%s AND organization_id=%s AND role_key='trip_editor' "
            "AND revoked_at IS NULL",
            (str(account), str(org)),
        )
        row = await cur.fetchone()
        return report, int(str(row[0])) if row else -1

    report, count = run_as_owner(scenario)
    assert count == 1, "overlapping role was duplicated on migration"
    assert not report.duplicated


def test_migration_refuses_to_merge_a_user_into_itself() -> None:
    same = uuid.uuid4()

    async def scenario() -> None:
        await migrate_guest_to_account(
            _NullCursor(), guest_user_id=same, account_user_id=same, actor_id=same
        )

    with pytest.raises(ValueError):
        asyncio.run(scenario())


# --- provisioning must not weaken the STEP-002.01 boundary -------------------


@requires_db
def test_provisioning_does_not_weaken_rls() -> None:
    """R7's guarantee must survive this sub-step.

    Provisioning runs as the table owner. This asserts that privilege did not leak:
    the application role still cannot bypass RLS, and FORCE is still set.
    """

    async def scenario(
        cur: psycopg.AsyncCursor[tuple[object, ...]],
    ) -> tuple[object, int]:
        await cur.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname='journeylab_app'")
        row1 = await cur.fetchone()
        await cur.execute(
            "SELECT count(*) FROM pg_class WHERE relname IN "
            "('memberships','service_identities','organizations') AND relforcerowsecurity"
        )
        row2 = await cur.fetchone()
        return (row1[0] if row1 else None, int(str(row2[0])) if row2 else -1)

    bypass, forced = run_as_owner(scenario)
    assert bypass is False, "journeylab_app gained BYPASSRLS"
    assert forced == 3, f"FORCE RLS lost on {3 - forced} table(s)"


@requires_db
def test_audit_records_name_both_actor_and_subject() -> None:
    """§8 requires provisioning and revocation to be audited with who and what."""
    org = uuid.uuid4()

    async def scenario(cur: psycopg.AsyncCursor[tuple[object, ...]]) -> list[AuditRecord]:
        owner = await make_user(cur)
        await bind_tenant(cur, RequestContext(actor_id=owner, organization_id=org))
        created = await create_organization(
            cur, organization_id=org, slug=unique("org"), display_name="O", owner_user_id=owner
        )
        granted = await grant_membership(
            cur, organization_id=org, user_id=owner, role_key="trip_viewer", actor_id=owner
        )
        revoked = await revoke_membership(
            cur, organization_id=org, user_id=owner, role_key="trip_viewer", actor_id=owner
        )
        return [created, granted, revoked]

    for record in run_as_owner(scenario):
        assert record.actor_id is not None, f"{record.action} has no actor"
        assert record.subject, f"{record.action} has no subject"
        assert record.occurred_at.tzinfo is not None, f"{record.action} timestamp is naive"
        assert re.match(r"^[a-z_]+\.[a-z_]+$", record.action), record.action
