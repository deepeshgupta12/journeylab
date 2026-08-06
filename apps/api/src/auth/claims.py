"""Token claims and the verifier port — STEP-002.02.

DEC-004 (identity provider: managed OIDC vs. self-hosted) is OPEN and binds at
STEP-002.04. This module therefore defines a *port*, not a vendor integration:
`TokenVerifier` is the seam the real provider plugs into. Nothing here imports an
SDK, and nothing here decides the decision.

REQ-SEC-001, REQ-SEC-004.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class TokenError(Exception):
    """Raised when a token cannot be verified.

    Deliberately carries no detail about *why*. The boundary converts this into a
    response that is indistinguishable from "not found" (see errors.py); an
    exception message that distinguishes "expired" from "wrong tenant" would
    re-introduce the oracle that indistinguishability exists to remove.
    """


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """The verified claims of a bearer token.

    Frozen: once verified, claims are evidence. Code that could mutate the tenant
    after verification would defeat the entire control, so the type forbids it.
    """

    subject: uuid.UUID
    organization_id: uuid.UUID

    def __post_init__(self) -> None:
        # A UUID-typed field can still be handed a string by untyped call sites
        # (a verifier implementation parsing JSON, for example). mypy catches that
        # statically; this catches it at the boundary where the cost of being
        # wrong is cross-tenant exposure.
        if not isinstance(self.subject, uuid.UUID):
            raise TokenError("subject is not a UUID")
        if not isinstance(self.organization_id, uuid.UUID):
            raise TokenError("organization_id is not a UUID")


@runtime_checkable
class TokenVerifier(Protocol):
    """Verifies a raw bearer token and returns its claims.

    Implementations MUST validate signature, issuer, audience and expiry, and MUST
    raise `TokenError` on any failure. Returning unverified claims would make every
    downstream tenancy control decorative.
    """

    def verify(self, raw_token: str) -> TokenClaims:
        """Return verified claims, or raise `TokenError`."""
        ...
