"""Indistinguishable authorization failures — STEP-002.02.

WHY 403 AND 404 MUST LOOK IDENTICAL
    If "you may not see this trip" and "no such trip" are distinguishable, the API
    is an existence oracle: an attacker enumerates identifiers and learns which
    ones are real in another tenant. The resource is protected; its existence is
    not.

    So both cases return the SAME status, the SAME body and the SAME headers. The
    only place the distinction survives is the server-side audit record, where it
    is needed for investigation and cannot be observed by the caller.

REQ-SEC-004. Acceptance criterion: "403/404 indistinguishable."
"""

from __future__ import annotations

from typing import Any, Final

from fastapi import HTTPException

# One status for both meanings. 404 is chosen over 403 deliberately: a 403 still
# discloses that *something* is there to be forbidden.
OPAQUE_STATUS: Final = 404

OPAQUE_BODY: Final[dict[str, Any]] = {
    "error": {
        "code": "not_found",
        "message": "The requested resource does not exist or is not available.",
    }
}


def opaque_denial() -> HTTPException:
    """The single denial used for missing context, failed auth and cross-tenant access.

    Returned (not raised) so call sites read `raise opaque_denial()`, which keeps
    the raise visible at the point of decision.

    Note there is no `reason` parameter. An optional detail argument is exactly how
    indistinguishability erodes: one caller passes "wrong tenant" for debugging, it
    ships, and the oracle is back. The type system should not permit it.
    """
    return HTTPException(status_code=OPAQUE_STATUS, detail=OPAQUE_BODY)
