"""Request context and EXPLICIT propagation — STEP-002.02.

THE CENTRAL DESIGN CONSTRAINT
    The sub-step record names the failure mode directly: "Ambient context
    (thread-locals, contextvars) crossing an async boundary is the classic leak —
    propagation must be explicit and tested."

    So this module deliberately does NOT provide a module-level "current context"
    lookup. There is no `get_current_context()`, no ContextVar, no thread-local.
    Context is a value that is passed. If a function needs the tenant, it takes a
    `RequestContext` argument, and the type checker enforces that at every call
    site.

    That is a real ergonomic cost — every layer must thread the parameter through.
    It is accepted on purpose. Ambient state is convenient precisely because it
    crosses boundaries you did not think about, which is the same property that
    makes it leak across tenants.

REQ-SEC-001, REQ-SEC-004.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Final

from .claims import TokenClaims

_JOB_KEY: Final = "_journeylab_context"
_SCHEMA_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Who is acting, and in which tenant.

    Frozen for the same reason `TokenClaims` is: this value is the authority for
    every tenancy decision downstream. A mutable context is a context that can be
    changed after the check and before the use.
    """

    actor_id: uuid.UUID
    organization_id: uuid.UUID

    @classmethod
    def from_claims(cls, claims: TokenClaims) -> RequestContext:
        """Build context from verified claims.

        This is the ONLY constructor used at the request boundary, and it reads
        exclusively from the token. There is no code path that lets a header, query
        parameter or body field influence the tenant — not because callers are
        trusted to avoid it, but because no such parameter exists to pass.
        """
        return cls(actor_id=claims.subject, organization_id=claims.organization_id)

    # -- crossing an async / process boundary ------------------------------------
    #
    # Background jobs and workflow activities do not inherit context. They must
    # carry it as data. These two methods are that carriage, and they are
    # symmetric so a round trip is testable.

    def to_job_payload(self) -> dict[str, Any]:
        """Serialise context for a job payload or activity input.

        Versioned: a worker running older code must be able to recognise a payload
        it cannot safely interpret, rather than silently reading the wrong field.
        """
        return {
            _JOB_KEY: {
                "v": _SCHEMA_VERSION,
                "actor_id": str(self.actor_id),
                "organization_id": str(self.organization_id),
            }
        }

    @classmethod
    def from_job_payload(cls, payload: dict[str, Any]) -> RequestContext:
        """Recover context from a job payload, or fail closed.

        Every failure mode here raises. A job that runs *without* tenant context
        would either see nothing (deny-by-default at the database, per STEP-002.01)
        or, worse, run as an identity the caller never had. Neither is something to
        paper over with a default.
        """
        raw = payload.get(_JOB_KEY)
        if not isinstance(raw, dict):
            raise ValueError("job payload carries no tenant context")
        if raw.get("v") != _SCHEMA_VERSION:
            raise ValueError(f"unsupported context schema version: {raw.get('v')!r}")
        try:
            return cls(
                actor_id=uuid.UUID(str(raw["actor_id"])),
                organization_id=uuid.UUID(str(raw["organization_id"])),
            )
        except (KeyError, ValueError) as exc:
            raise ValueError("job payload context is malformed") from exc

    def __str__(self) -> str:
        """Redacted by default.

        STEP-002.02 §8 requires telemetry to carry no PII and correlation IDs to be
        tenant-safe. The most common way identifiers reach a log is an f-string on
        the context object, so the default rendering must already be safe.
        """
        return f"RequestContext(org=…{str(self.organization_id)[-4:]}, actor=…{str(self.actor_id)[-4:]})"

    __repr__ = __str__
