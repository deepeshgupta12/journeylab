"""Tenant and actor context resolution at the API boundary — STEP-002.02."""

from .claims import TokenClaims, TokenError, TokenVerifier
from .context import RequestContext
from .db import bind_tenant
from .dependencies import make_context_dependency
from .errors import OPAQUE_BODY, OPAQUE_STATUS, opaque_denial
from .events import stamp_envelope

__all__ = [
    "OPAQUE_BODY",
    "OPAQUE_STATUS",
    "RequestContext",
    "TokenClaims",
    "TokenError",
    "TokenVerifier",
    "bind_tenant",
    "make_context_dependency",
    "opaque_denial",
    "stamp_envelope",
]
