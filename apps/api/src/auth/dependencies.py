"""FastAPI dependency resolving actor and tenant — STEP-002.02.

This is the file the sub-step names. Everything else in `auth/` exists to let this
be short, because this is the function whose correctness the tenancy model rests
on.

THE ONE RULE
    The tenant comes from the token. Nothing else. This function does not read
    `X-Tenant-Id`, `?org=`, a body field or a cookie — and the way that is
    guaranteed is not review discipline but absence: the request object is never
    consulted for anything except the Authorization header.

REQ-SEC-001, REQ-SEC-004. Tests: TST-SEC-001, TST-SEC-004.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request

from .claims import TokenError, TokenVerifier
from .context import RequestContext
from .errors import opaque_denial

ContextDependency = Callable[[Request], Awaitable[RequestContext]]

_SCHEME = "bearer"


def _extract_bearer(request: Request) -> str:
    """Pull the raw token out of the Authorization header, or fail closed."""
    header = request.headers.get("authorization")
    if not header:
        raise opaque_denial()
    scheme, _, token = header.partition(" ")
    if scheme.lower() != _SCHEME or not token.strip():
        raise opaque_denial()
    return token.strip()


def make_context_dependency(verifier: TokenVerifier) -> ContextDependency:
    """Build the request dependency, closing over a token verifier.

    A factory rather than a module-level singleton so the verifier is injected.
    That is what keeps DEC-004 open: swapping the identity provider at STEP-002.04
    changes the argument passed here and nothing else.
    """

    async def resolve_context(request: Request) -> RequestContext:
        raw = _extract_bearer(request)
        try:
            claims = verifier.verify(raw)
        except TokenError:
            # Deliberately swallowed. Any distinction leaked here — expired vs.
            # malformed vs. unknown signer — is an oracle. The audit record is the
            # place for detail; the response is not.
            raise opaque_denial() from None
        return RequestContext.from_claims(claims)

    return resolve_context
