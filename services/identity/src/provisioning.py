"""Identity lifecycle — STEP-002.04 (REQ-SEC-003, REQ-TRIP-005).

Users, organizations, memberships and service identities are created, granted and
revoked here. Nothing else writes to those tables.

VENDOR NEUTRALITY IS A REQUIREMENT, NOT A STYLE
    `DEC-004` (managed OIDC vs. self-hosted) is open, and §5 of the sub-step
    requires provider-specific code to stay behind an interface so the decision
    stays reversible. This module therefore never imports a provider SDK and never
    branches on one. Its only knowledge of the identity provider is the opaque
    `idp_subject` string that `auth.claims.TokenVerifier` already produces. Picking
    a vendor should change the verifier and nothing here.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
    - It does not store credentials. `service_identities` has no secret column, and
      a test asserts the schema keeps it that way (REQ-SEC-003).
    - It does not persist audit records. There is no audit sink until STEP-002.07,
      so every mutating call RETURNS an `AuditRecord` the caller must write.
      Returning it rather than logging it means the obligation cannot be forgotten
      silently — the value is in the caller's hands.
    - It does not invalidate tokens. Revocation marks state; making a live session
      stop is STEP-002.05.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class _Cursor(Protocol):
    """The slice of an async DB-API cursor this module uses.

    Structural, matching `auth.db._Cursor`, so the driver choice (ADR-011) does not
    spread further than it must and the logic stays unit-testable.
    """

    async def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    async def fetchone(self) -> tuple[object, ...] | None: ...
    async def fetchall(self) -> list[tuple[object, ...]]: ...


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """What happened, to be persisted by the caller (STEP-002.07).

    `subject` is the thing acted upon; `actor_id` is who acted. Both are needed:
    "membership revoked" without an actor is not an audit record, it is a rumour.
    """

    action: str
    actor_id: uuid.UUID | None
    organization_id: uuid.UUID | None
    subject: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ProvisionedUser:
    user_id: uuid.UUID
    created: bool
    audit: AuditRecord


@dataclass(frozen=True, slots=True)
class MigrationReport:
    """Before/after counts, because §8 requires duplication to be *detectable*."""

    guest_user_id: uuid.UUID
    account_user_id: uuid.UUID
    memberships_before_guest: int
    memberships_before_account: int
    memberships_moved: int
    memberships_after_account: int
    already_migrated: bool
    audit: AuditRecord

    @property
    def duplicated(self) -> bool:
        """True if the account ended up with more rows than the union could justify.

        The unique constraint on (organization_id, user_id, role_key) makes literal
        duplicates impossible, so this is a belt-and-braces check on the arithmetic
        rather than on the database — if it ever fires, the logic is wrong even
        though the schema held.
        """
        return self.memberships_after_account > (
            self.memberships_before_account + self.memberships_before_guest
        )


def _now() -> datetime:
    return datetime.now(UTC)


# --- users -------------------------------------------------------------------


async def provision_user(
    cur: _Cursor,
    *,
    idp_subject: str,
    email: str | None = None,
    locale: str = "en",
    time_zone: str = "UTC",
) -> ProvisionedUser:
    """Create the user for `idp_subject`, or return the existing one.

    Idempotent **at the database**, not by check-then-insert. Two concurrent first
    logins for the same subject race in the application; `ON CONFLICT` lets the
    database arbitrate, and the loser gets the winner's row instead of a duplicate
    identity. `users.idp_subject` carries a unique index, which is what makes this
    safe — verified against the live schema rather than assumed.

    `xmax = 0` distinguishes an inserted row from an updated one, so the caller can
    tell first login from every later one without a second query.
    """
    if not idp_subject.strip():
        raise ValueError("idp_subject must be a non-empty string")

    await cur.execute(
        """
        INSERT INTO users (idp_subject, email, locale, time_zone, is_guest)
        VALUES (%s, %s, %s, %s, false)
        ON CONFLICT (idp_subject) DO UPDATE
            SET updated_at = now(),
                email      = COALESCE(EXCLUDED.email, users.email)
        RETURNING id, (xmax = 0) AS created
        """,
        (idp_subject, email, locale, time_zone),
    )
    row = await cur.fetchone()
    if row is None:  # pragma: no cover - RETURNING always yields a row here
        raise RuntimeError("provision_user: INSERT ... RETURNING produced no row")

    user_id, created = uuid.UUID(str(row[0])), bool(row[1])
    return ProvisionedUser(
        user_id=user_id,
        created=created,
        audit=AuditRecord(
            action="user.provisioned" if created else "user.reauthenticated",
            actor_id=user_id,
            organization_id=None,
            subject=f"user:{user_id}",
            occurred_at=_now(),
        ),
    )


async def create_guest_user(
    cur: _Cursor, *, locale: str = "en", time_zone: str = "UTC"
) -> uuid.UUID:
    """Create an anonymous guest.

    A guest has no `idp_subject`. That is deliberate and is why the unique index
    tolerates it: Postgres permits many NULLs in a unique index, so guests do not
    collide with each other while authenticated users still cannot.
    """
    await cur.execute(
        "INSERT INTO users (idp_subject, email, locale, time_zone, is_guest) "
        "VALUES (NULL, NULL, %s, %s, true) RETURNING id",
        (locale, time_zone),
    )
    row = await cur.fetchone()
    if row is None:  # pragma: no cover
        raise RuntimeError("create_guest_user: no row returned")
    return uuid.UUID(str(row[0]))


# --- organizations and memberships -------------------------------------------


async def create_organization(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    slug: str,
    display_name: str,
    owner_user_id: uuid.UUID,
) -> AuditRecord:
    """Create an organization together with its owner membership.

    `organization_id` is supplied by the caller rather than defaulted by the
    database. That is forced by the RLS policy from STEP-002.01:

        WITH CHECK (id = app_current_org())

    An organization can only be inserted when the transaction's tenant context
    already equals its id — so the id has to exist before the INSERT, and the
    caller must have bound it with `auth.db.bind_tenant`. A server-generated id
    could not satisfy its own policy.

    Owner membership is created in the same call because an organization with no
    owner is unreachable: RLS admits only members, so nobody could ever grant the
    first one.
    """
    await cur.execute(
        "INSERT INTO organizations (id, slug, display_name) VALUES (%s, %s, %s)",
        (str(organization_id), slug, display_name),
    )
    await cur.execute(
        "INSERT INTO memberships (organization_id, user_id, role_key) VALUES (%s, %s, 'trip_owner') "
        "ON CONFLICT (organization_id, user_id, role_key) DO NOTHING",
        (str(organization_id), str(owner_user_id)),
    )
    return AuditRecord(
        action="organization.created",
        actor_id=owner_user_id,
        organization_id=organization_id,
        subject=f"organization:{organization_id}",
        occurred_at=_now(),
    )


async def grant_membership(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role_key: str,
    actor_id: uuid.UUID,
    expires_at: datetime | None = None,
) -> AuditRecord:
    """Grant a role, or reinstate a previously revoked one.

    `DO UPDATE ... revoked_at = NULL` is a deliberate re-grant: without it a revoked
    membership would block its own reinstatement through the unique constraint, and
    the operator would be left deleting rows by hand.
    """
    if expires_at is not None and expires_at.tzinfo is None:
        raise ValueError("expires_at must be timezone-aware")

    await cur.execute(
        """
        INSERT INTO memberships (organization_id, user_id, role_key, expires_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (organization_id, user_id, role_key) DO UPDATE
            SET revoked_at = NULL, expires_at = EXCLUDED.expires_at
        """,
        (str(organization_id), str(user_id), role_key, expires_at),
    )
    return AuditRecord(
        action="membership.granted",
        actor_id=actor_id,
        organization_id=organization_id,
        subject=f"user:{user_id}:{role_key}",
        occurred_at=_now(),
    )


async def revoke_membership(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role_key: str,
    actor_id: uuid.UUID,
) -> AuditRecord:
    """Revoke a role by stamping `revoked_at`, never by deleting the row.

    Deleting would erase the evidence that access was once held, which is exactly
    what an investigation needs. Revoked rows remain and readers must filter them.
    """
    await cur.execute(
        "UPDATE memberships SET revoked_at = now() "
        "WHERE organization_id = %s AND user_id = %s AND role_key = %s AND revoked_at IS NULL",
        (str(organization_id), str(user_id), role_key),
    )
    return AuditRecord(
        action="membership.revoked",
        actor_id=actor_id,
        organization_id=organization_id,
        subject=f"user:{user_id}:{role_key}",
        occurred_at=_now(),
    )


async def active_role_keys(
    cur: _Cursor, *, organization_id: uuid.UUID, user_id: uuid.UUID, now: datetime | None = None
) -> frozenset[str]:
    """Roles currently in force — revoked and expired excluded.

    The single place "is this membership live?" is decided. A caller reading
    `memberships` directly would have to remember both `revoked_at` and
    `expires_at`, and forgetting either grants access that should have ended.
    """
    moment = now or _now()
    await cur.execute(
        "SELECT role_key FROM memberships "
        "WHERE organization_id = %s AND user_id = %s "
        "  AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > %s)",
        (str(organization_id), str(user_id), moment),
    )
    return frozenset(str(r[0]) for r in await cur.fetchall())


# --- service identities ------------------------------------------------------


async def register_service_identity(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    name: str,
    workload_subject: str,
    actor_id: uuid.UUID,
) -> AuditRecord:
    """Register a workload identity. No secret is accepted, stored or returned.

    REQ-SEC-003 forbids static long-lived keys. This function has no parameter
    through which one could be supplied, which is a stronger guarantee than a
    policy telling people not to: there is nowhere to put it.

    `workload_subject` is the identity the platform attests (a Kubernetes service
    account, an instance identity document, an OIDC workload subject). It is a
    *name*, not a credential — possessing the string grants nothing.
    """
    await cur.execute(
        "INSERT INTO service_identities (organization_id, name, workload_subject) "
        "VALUES (%s, %s, %s) "
        "ON CONFLICT (organization_id, name) DO UPDATE "
        "  SET workload_subject = EXCLUDED.workload_subject, revoked_at = NULL",
        (str(organization_id), name, workload_subject),
    )
    return AuditRecord(
        action="service_identity.registered",
        actor_id=actor_id,
        organization_id=organization_id,
        subject=f"service:{name}",
        occurred_at=_now(),
    )


async def revoke_service_identity(
    cur: _Cursor, *, organization_id: uuid.UUID, name: str, actor_id: uuid.UUID
) -> AuditRecord:
    await cur.execute(
        "UPDATE service_identities SET revoked_at = now() "
        "WHERE organization_id = %s AND name = %s AND revoked_at IS NULL",
        (str(organization_id), name),
    )
    return AuditRecord(
        action="service_identity.revoked",
        actor_id=actor_id,
        organization_id=organization_id,
        subject=f"service:{name}",
        occurred_at=_now(),
    )


# --- guest to account migration ----------------------------------------------

# Column names that would indicate a stored credential. `role_key` and
# `idp_subject` are deliberately absent: they are identifiers, not secrets.
CREDENTIAL_COLUMN_PATTERN = re.compile(
    r"(secret|password|passwd|api_?key|private_?key|access_?token|refresh_?token|credential)",
    re.IGNORECASE,
)


async def migrate_guest_to_account(
    cur: _Cursor,
    *,
    guest_user_id: uuid.UUID,
    account_user_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> MigrationReport:
    """Re-parent a guest's holdings onto a real account. Safe to replay.

    REQ-TRIP-005 requires exactly one copy of each trip. Idempotency is the whole
    requirement here, and the sub-step names why: "a retried migration that
    duplicates trips is indistinguishable from a user creating them" — nobody can
    tell afterwards which copies were the bug.

    So the move is expressed as `INSERT … ON CONFLICT DO NOTHING` followed by
    revoking the source rows. Replaying finds nothing left to move and reports
    `already_migrated`, rather than moving anything a second time.

    SCOPE, STATED PLAINLY: there is no `trips` table yet — trips arrive at STEP-007.
    What migrates today is **memberships**. The idempotency contract and its tests
    are built here so that adding trips is a matter of extending the same
    transaction, not inventing the guarantee later. Recorded in BR-013 §9.
    """
    if guest_user_id == account_user_id:
        raise ValueError("cannot migrate a user onto itself")

    before_guest = await _membership_count(cur, guest_user_id, include_revoked=False)
    before_account = await _membership_count(cur, account_user_id, include_revoked=False)

    await cur.execute(
        """
        INSERT INTO memberships (organization_id, user_id, role_key, expires_at)
        SELECT organization_id, %s, role_key, expires_at
          FROM memberships
         WHERE user_id = %s AND revoked_at IS NULL
        ON CONFLICT (organization_id, user_id, role_key) DO NOTHING
        """,
        (str(account_user_id), str(guest_user_id)),
    )
    await cur.execute(
        "UPDATE memberships SET revoked_at = now() WHERE user_id = %s AND revoked_at IS NULL",
        (str(guest_user_id),),
    )

    after_account = await _membership_count(cur, account_user_id, include_revoked=False)
    return MigrationReport(
        guest_user_id=guest_user_id,
        account_user_id=account_user_id,
        memberships_before_guest=before_guest,
        memberships_before_account=before_account,
        memberships_moved=after_account - before_account,
        memberships_after_account=after_account,
        already_migrated=before_guest == 0,
        audit=AuditRecord(
            action="guest.migrated",
            actor_id=actor_id,
            organization_id=None,
            subject=f"guest:{guest_user_id}->account:{account_user_id}",
            occurred_at=_now(),
        ),
    )


async def _membership_count(cur: _Cursor, user_id: uuid.UUID, *, include_revoked: bool) -> int:
    clause = "" if include_revoked else " AND revoked_at IS NULL"
    await cur.execute(
        f"SELECT count(*) FROM memberships WHERE user_id = %s{clause}",  # noqa: S608 - literal clause
        (str(user_id),),
    )
    row = await cur.fetchone()
    return int(str(row[0])) if row else 0
