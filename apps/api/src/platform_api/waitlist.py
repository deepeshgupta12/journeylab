"""Asking to be told when a destination opens — STEP-007.04.

WHAT THIS MODULE IS FOR
    Somebody read `/coverage`, learned their destination is not supported, and asked
    to hear about it when it is. That is the entire feature. It is small, and it is
    the first place in this product where a stranger's personal data is written by an
    unauthenticated request, which is why it has more comment than code.

THE SUBJECT HAS NO ACCOUNT, SO `consent_records` CANNOT HOLD THIS
    `DATA-016` is `organization_id NOT NULL, user_id NOT NULL` under row-level
    security, and `STEP-008.04` owns it. A waitlist subject has neither column's
    value. `019_waitlist.sql` §1 records the reasoning; the short version is that the
    alternatives were to invent an organization or to make the isolation columns
    nullable on the one table holding consent.

CONSENT IS AN ACTION, NOT A DEFAULT
    `granted` has no default anywhere in this path — not in the schema, not in the
    request model, not here. A request that omits it is refused, and a request that
    sends `false` is refused with the field named. There is deliberately no code path
    in which an entry is written because consent was *assumed*, and
    `join_waitlist` cannot be called without an explicit decision.

THE ADDRESS IS NEVER LOGGED, ECHOED OR RAISED
    §8 of the sub-step: the email is personal data from the moment it is typed, and
    must not reach a log line, a trace attribute or an event payload. It must also
    not reach a *problem document* — `BUG-035` was exactly this, an unauthenticated
    endpoint echoing the value that failed validation back to whoever sent it.

    So every exception this module raises names the FIELD and never its content. The
    tests assert that on the address specifically, because it is the one value here
    that identifies a person.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime

from platform_api.coverage import Cursor

#: The one purpose this table accepts, matching the CHECK in `019_waitlist.sql`.
#:
#: `REQ-PRIV-002` requires purpose-specific consent. A `purpose` column accepting any
#: string is a column that eventually holds `'marketing'` because somebody passed it,
#: so the value is constrained in three places that cannot disagree: the enum in the
#: contract, the constant here, and the database CHECK.
WAITLIST_PURPOSE = "waitlist_notification"

#: `REQ-PRIV-002`: the lawful basis is recorded with the grant, not inferred later.
WAITLIST_BASIS = "consent"

#: RFC 5321 caps a path at 256 octets including the angle brackets, so 254 is the
#: longest address that can exist. Bounded because this endpoint is unauthenticated:
#: an unbounded string is something anyone can send, and it reaches a database column
#: and a uniqueness index.
EMAIL_MAX_LENGTH = 254

#: `a@b` is the shortest thing that could conceivably be one.
EMAIL_MIN_LENGTH = 3

#: Mirrors `waitlist_region_query_bounded`. What the person was searching for when
#: they were turned away — free text, because the region is by definition not one we
#: have an identifier for.
REGION_QUERY_MAX_LENGTH = 64

#: 32 bytes from `secrets`. This is the entire authorisation for withdrawal, so it is
#: sized as a secret rather than as an identifier: guessing one must be infeasible,
#: because a guessed token withdraws somebody else's consent.
WITHDRAWAL_TOKEN_BYTES = 32


class WaitlistError(RuntimeError):
    """A request that cannot be accepted.

    The message names fields, never values. See the module docstring: this reaches a
    problem document on an unauthenticated endpoint, and `BUG-035` is what happens
    when such a document quotes its input back.
    """

    def __init__(self, message: str, *, fields: tuple[str, ...]) -> None:
        super().__init__(message)
        #: For `remediation.correct_fields`, so a client can highlight the input.
        self.fields = fields


@dataclass(frozen=True, slots=True)
class WaitlistGrant:
    """A recorded consent, and the one-time capability to withdraw it."""

    purpose: str
    basis: str
    granted_at: datetime
    #: Returned to the caller exactly once and never stored in this form. The
    #: database holds `sha256(token)`; see `token_hash`.
    withdrawal_token: str


@dataclass(frozen=True, slots=True)
class WaitlistWithdrawal:
    """A consent that is no longer in force, and an address that no longer exists."""

    purpose: str
    withdrawn_at: datetime
    #: True when this call is what withdrew it; False when it was already withdrawn.
    #: Both are successes — see `withdraw_waitlist_consent`.
    changed: bool


def token_hash(token: str) -> str:
    """SHA-256, hex.

    Not a password hash, and deliberately not one. A KDF exists to make guessing a
    LOW-entropy secret expensive; this secret has 256 bits of entropy from
    `secrets.token_urlsafe`, so there is nothing to slow down, and a per-verification
    KDF on an unauthenticated endpoint is a denial-of-service lever pointed at
    ourselves.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def mint_withdrawal_token() -> str:
    """A fresh capability. `secrets`, never `random`."""
    return secrets.token_urlsafe(WITHDRAWAL_TOKEN_BYTES)


def normalise_email(raw: str) -> str:
    """The form used for uniqueness: trimmed and lowercased.

    Stored ALONGSIDE what the person typed rather than instead of it. The local part
    of an address is case-sensitive under RFC 5321 even though effectively no
    operator treats it that way, so lowercasing for comparison is right and
    lowercasing for delivery is a small liberty taken with somebody's name.
    """
    return raw.strip().lower()


def validate_email(raw: str) -> str:
    """Return the address as typed, trimmed — or raise naming the field.

    DELIBERATELY NOT A REGEX FOR RFC 5322
        The grammar admits quoted strings, comments and address literals, and every
        "email regex" in circulation is wrong in both directions. Worse, a permissive
        pattern applied to attacker-controlled input is a place for catastrophic
        backtracking.

        What this checks is what this system actually needs: one `@`, something on
        each side of it, a dot in the domain, no whitespace or control characters,
        and a bounded length. An address that passes this and does not exist is
        caught by delivery failing — which is the only check that ever really
        settles it, and which is out of scope for this sub-step.
    """
    address = raw.strip()

    if not (EMAIL_MIN_LENGTH <= len(address) <= EMAIL_MAX_LENGTH):
        raise WaitlistError(
            f"An email address must be between {EMAIL_MIN_LENGTH} and "
            f"{EMAIL_MAX_LENGTH} characters.",
            fields=("email",),
        )

    if any(character.isspace() or ord(character) < 0x20 for character in address):
        raise WaitlistError(
            "An email address may not contain spaces or control characters.",
            fields=("email",),
        )

    local, separator, domain = address.partition("@")
    if not separator or not local or not domain or "@" in domain:
        raise WaitlistError(
            "An email address needs exactly one @, with text on both sides.",
            fields=("email",),
        )

    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise WaitlistError(
            "The domain of an email address needs a dot, and cannot start or end with one.",
            fields=("email",),
        )

    return address


def validate_region_query(raw: str | None) -> str | None:
    """The destination they were looking for. Optional, bounded, never required."""
    if raw is None:
        return None
    query = raw.strip()
    if not query:
        return None
    if len(query) > REGION_QUERY_MAX_LENGTH:
        raise WaitlistError(
            f"A destination may be at most {REGION_QUERY_MAX_LENGTH} characters.",
            fields=("region_query",),
        )
    return query


def require_consent(*, purpose: str, granted: bool) -> None:
    """`REQ-PRIV-002`, `REQ-PRIV-004`: the grant is explicit or there is no entry.

    Two refusals rather than one, because they are different mistakes: a client
    asking for a purpose this endpoint does not serve is a contract error, and a
    client sending `granted: false` is a person who did not agree. Collapsing them
    would make the second unreadable in a client that shows the message.
    """
    if purpose != WAITLIST_PURPOSE:
        raise WaitlistError(
            f"This endpoint records one purpose only: {WAITLIST_PURPOSE}.",
            fields=("consent.purpose",),
        )
    if not granted:
        raise WaitlistError(
            "A waitlist entry requires consent to be contacted for that purpose. "
            "Nothing has been stored.",
            fields=("consent.granted",),
        )


def join_waitlist(
    cursor: Cursor,
    *,
    email: str,
    region_query: str | None,
    purpose: str,
    granted: bool,
    now: datetime,
) -> WaitlistGrant:
    """Record a purpose-specific grant and return its one-time withdrawal token.

    VALIDATION HAPPENS BEFORE ANYTHING IS WRITTEN
        Consent is checked first, then the address. A request that fails either one
        leaves no row, which is what makes "a waitlist entry without a consent record
        is refused" a property of the code rather than a claim about it.

    A REPEATED JOIN ROTATES THE TOKEN RATHER THAN CREATING A SECOND ROW
        `waitlist_active_email_idx` allows one active entry per address. A second
        join for an address already on the list therefore cannot insert, and there
        are only two things it can do, because **only the hash of the first token was
        kept — the original cannot be handed back.**

        So it rotates: the grant timestamp is left alone (the original consent is
        when consent was given), and a fresh token replaces the old hash.

        THE TRADE THIS MAKES, STATED PLAINLY. Until an address is verified — which
        needs email delivery, explicitly out of scope here — anyone who knows an
        address can rotate its token and then withdraw that entry. The ceiling on
        that is removing an address from a notification list; no personal data is
        disclosed by the response, which is identical either way and therefore does
        not reveal whether the address was already present. Recorded as a follow-up
        to be closed by verification, not left to be discovered.
    """
    require_consent(purpose=purpose, granted=granted)
    address = validate_email(email)
    destination = validate_region_query(region_query)

    token = mint_withdrawal_token()

    # ON CONFLICT on the PARTIAL index, so a withdrawn row never blocks a rejoin.
    #
    # `granted_at` is excluded from the update on purpose: re-submitting a form does
    # not re-date a consent that was given days ago, and moving it would quietly
    # extend any retention measured from it.
    cursor.execute(
        """
        INSERT INTO waitlist_entries (
            email, email_normalized, region_query,
            purpose, basis, granted_at, withdrawal_token_hash
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email_normalized) WHERE withdrawn_at IS NULL
        DO UPDATE SET
            withdrawal_token_hash = EXCLUDED.withdrawal_token_hash,
            region_query          = COALESCE(EXCLUDED.region_query, waitlist_entries.region_query),
            email                 = EXCLUDED.email
        RETURNING purpose, basis, granted_at
        """,
        (
            address,
            normalise_email(address),
            destination,
            WAITLIST_PURPOSE,
            WAITLIST_BASIS,
            now,
            token_hash(token),
        ),
    )
    # `fetchall`, not `fetchone`: the shared `Cursor` protocol declares `execute` and
    # `fetchall` only, and widening it to serve this module would change the contract
    # every other reader is written against.
    rows = cursor.fetchall()
    if not rows:  # pragma: no cover - RETURNING on an upsert always yields a row
        raise WaitlistError("The waitlist entry could not be recorded.", fields=())

    purpose_stored, basis_stored, granted_at = rows[0]
    return WaitlistGrant(
        purpose=str(purpose_stored),
        basis=str(basis_stored),
        granted_at=granted_at,
        withdrawal_token=token,
    )


def withdraw_waitlist_consent(
    cursor: Cursor,
    *,
    token: str,
    now: datetime,
) -> WaitlistWithdrawal | None:
    """Withdraw one grant and destroy the address. `None` when the token is unknown.

    WHAT SURVIVES AND WHAT DOES NOT
        `withdrawn_at` is set and `email` / `email_normalized` are set to NULL in the
        same statement. The grant remains as evidence that processing was once
        lawful — `STEP-008.04`'s rule — while the personal data that made it
        identifiable is gone, which is `REQ-PRIV-006`. The CHECK constraint
        `waitlist_active_has_address` means a version of this that forgot the second
        half would fail to commit rather than leave an address behind a withdrawal.

    WITHDRAWING TWICE IS A SUCCESS, NOT AN ERROR
        The second call finds a row that is already withdrawn and changes nothing.
        Reporting that as a failure would tell the holder of a valid token that
        something went wrong when the state they asked for is exactly the state that
        holds. `changed` distinguishes the two for anything that cares.

    THIS TOUCHES NOTHING ELSE — `REQ-PRIV-004`
        One row, matched by one token hash, and no other consent anywhere in the
        system is reachable from here. `consent_records` is a different table this
        module does not import, so withdrawal of a waitlist purpose cannot cascade
        into a purpose somebody granted separately.
    """
    presented = token_hash(token)

    cursor.execute(
        """
        UPDATE waitlist_entries
           SET withdrawn_at     = COALESCE(withdrawn_at, %s),
               email            = NULL,
               email_normalized = NULL
         WHERE withdrawal_token_hash = %s
        RETURNING purpose, withdrawn_at, (withdrawn_at = %s) AS changed
        """,
        (now, presented, now),
    )
    rows = cursor.fetchall()
    if not rows:
        # Unknown token. The caller turns this into `authz.forbidden`, whose register
        # entry reads "Identical to not-found" — so a probe cannot learn whether a
        # token existed.
        return None

    purpose, withdrawn_at, changed = rows[0]
    return WaitlistWithdrawal(
        purpose=str(purpose),
        withdrawn_at=withdrawn_at,
        changed=bool(changed),
    )
