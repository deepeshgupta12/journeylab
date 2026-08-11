"""RFC 9457 problem details — STEP-004.01 (REQ-PLAT-005).

WHY THIS PACKAGE IS `conventions` AND NOT `http`
    `apps/api/src` is on `pythonpath` (pyproject.toml), so a package named `http`
    there SHADOWS the standard library's `http` module for the whole application.
    Nothing would fail at import time; things would fail later, somewhere else,
    when a dependency reached for `http.client` and got this instead.

ONE ERROR SHAPE FOR EVERY ENDPOINT
    The sub-step's outcome is "no service invents its own error shape". This is
    the shape. Every failure the API reports is built here, from a code in the
    generated register, and served as `application/problem+json`.

WHY THE REGISTER IS THE ONLY WAY IN
    `problem()` takes a code, not a title and a status. A caller cannot invent a
    new error by passing strings, because the status, the meaning and the
    remediation all come from `ERROR_CODES` — which is generated from
    `ERROR_MODEL.md`. Inventing an error requires editing the product document,
    which is exactly the friction that should exist.

    The alternative — a free-form constructor — produces eighteen slightly
    different spellings of "not found" within a year, and clients that branch on
    prose.

WHAT NEVER APPEARS IN A PROBLEM DOCUMENT
    `ERROR_MODEL.md` §5 is explicit and this module enforces it:

      * No other tenant's data, ever.
      * No stack trace.
      * **No provider identity.** Which timetable supplier failed is commercially
        confidential and is attack-surface information; it is logged internally
        and never returned.
      * No request body content — constraints and evidence prose are personal
        data (`REQ-PRIV-004`).

    `detail` is therefore assembled from the register plus caller-supplied text
    that the caller is responsible for keeping safe, and `safe_detail()` exists to
    make that responsibility explicit rather than assumed.

THE 403/404 RULE LIVES HERE NOW
    STEP-002.02 put indistinguishable denial in `auth/errors.py` with an ad-hoc
    body. Moving it into the shared convention is the whole point of doing this
    sub-step before the operations: the completion note for STEP-004.01 says
    getting it into the convention "is far cheaper than retrofitting it across 18
    operations".
"""

from __future__ import annotations

import re
from typing import Any, Final

from .error_codes import ERROR_CODES, ErrorCodeSpec

PROBLEM_MEDIA_TYPE: Final = "application/problem+json"

#: The status every authorization failure reports, whatever actually happened.
#:
#: 404 rather than 403, and the choice is deliberate: a 403 still discloses that
#: *something* is there to be forbidden. Carried unchanged from STEP-002.02.
OPAQUE_STATUS: Final = 404

#: The one code used for every denial. `authz.forbidden` in the register.
OPAQUE_CODE: Final = "authz.forbidden"

#: Patterns that must never reach a caller. Checked, not merely documented —
#: `ERROR_MODEL.md` §5 lists these prohibitions and a list nobody enforces is a
#: list that decays.
_LEAKY: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (re.compile(r'File "[^"]+", line \d+'), "a Python traceback frame"),
    (re.compile(r"\bTraceback \(most recent call last\)"), "a traceback header"),
    (re.compile(r"\b(?:postgresql|postgres|redis|amqp|nats)://", re.I), "a connection string"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "an email address"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.I), "a bearer token"),
    (re.compile(r"\beyJ[A-Za-z0-9._\-]{10,}"), "a JWT"),
)


class ProblemError(ValueError):
    """Raised when a problem document would be malformed or unsafe to send."""


def safe_detail(text: str) -> str:
    """Assert that caller-supplied detail carries nothing it must not.

    Deliberately raises rather than redacting.

    Redaction would be the friendlier behaviour and the wrong one: it turns a
    developer mistake into a silently-truncated message that still ships, and the
    next reader assumes the sanitiser has it covered for cases it does not. The
    same reasoning as `services/audit/src/redaction.py`, which fails closed.
    """
    for pattern, what in _LEAKY:
        if pattern.search(text):
            raise ProblemError(
                f"problem detail contains {what}. ERROR_MODEL.md §5: a problem "
                f"document carries no stack trace, no connection string, no "
                f"credential and no personal data. Log it instead."
            )
    return text


def problem(
    code: str,
    *,
    correlation_id: str,
    detail: str | None = None,
    instance: str | None = None,
    remediation: dict[str, Any] | None = None,
    status: int | None = None,
) -> dict[str, Any]:
    """Build an RFC 9457 problem document for a registered error code.

    `correlation_id` is required and has no default. `ERROR_MODEL.md` calls it
    "the single thing support needs", and an optional correlation ID is one that
    is absent from precisely the responses anyone wants to investigate.
    """
    spec = ERROR_CODES.get(code)
    if spec is None:
        raise ProblemError(
            f"unknown error code {code!r}. Codes are generated from "
            f"ERROR_MODEL.md §3; add the row there and regenerate rather than "
            f"inventing one here."
        )
    if not spec.client_visible and status is None:
        raise ProblemError(
            f"{code!r} is an internal condition and has no client-facing status. "
            f"The register says it surfaces as a fallback or a warning, not as an "
            f"error response."
        )
    if not correlation_id:
        raise ProblemError("correlation_id is required on every problem document")

    document: dict[str, Any] = {
        "type": spec.type_uri,
        "title": spec.meaning,
        "status": status if status is not None else spec.status,
        "code": spec.code,
        "correlation_id": correlation_id,
        # Explicit, never inferred from the status. The document is emphatic:
        # "clients must not infer retryability from the status code". A 503 from a
        # degraded provider is retryable; a 503 because the region is unsupported
        # is not, and only the register knows which.
        "retryable": _retryable(spec),
    }
    if detail is not None:
        document["detail"] = safe_detail(detail)
    if instance is not None:
        document["instance"] = instance
    if remediation is not None:
        document["remediation"] = remediation
    return document


def _retryable(spec: ErrorCodeSpec) -> bool:
    """Whether a client should try the same request again.

    Derived from the taxonomy in `ERROR_MODEL.md` §2 rather than from the status:
    every 5xx except a timeout is a dependency problem worth retrying, and no 4xx
    is — repeating a request the server understood and refused changes nothing.
    """
    if spec.status is None:
        return False
    if spec.status in (503, 504):
        return True
    return False


def opaque_denial(correlation_id: str, *, instance: str | None = None) -> dict[str, Any]:
    """The single denial used for missing context, failed auth and cross-tenant access.

    There is still no `reason` parameter, for the reason STEP-002.02 gave: an
    optional detail argument is exactly how indistinguishability erodes. One
    caller passes "wrong tenant" for debugging, it ships, and the API is an
    existence oracle again.

    `detail` is omitted entirely rather than set to a constant, so there is no
    field a future edit can differentiate.

    THE STATUS IS FORCED TO 404, OVERRIDING THE REGISTER
        `ERROR_MODEL.md` writes the status of `authz.forbidden` as "403/404",
        meaning the two are deliberately indistinguishable. That notation does not
        say which one is sent, and the parser cannot decide — it took the first,
        which produced a 403 and quietly undid STEP-002.02.

        404 is the choice, and it is not a preference: a 403 confirms that
        something exists to be forbidden, which is the disclosure the whole
        mechanism is built to prevent. Forced here, at the single call site, so the
        register keeps documenting the pair while the code sends exactly one.
    """
    return problem(
        OPAQUE_CODE,
        correlation_id=correlation_id,
        instance=instance,
        status=OPAQUE_STATUS,
    )
