"""Cursor pagination — STEP-004.01 (REQ-PLAT-005).

OFFSET PAGINATION IS NOT SUPPORTED, AND THIS MODULE MAKES THAT STRUCTURAL
    `API_CONTRACTS.md` §1: "Cursor-based (`cursor`, `limit`); offset pagination is
    not supported." There is no `offset` parameter anywhere in this module, so a
    handler cannot accept one by copying the shape.

    The reason is correctness, not fashion. Offset pagination re-runs the query
    for every page, so a row inserted or deleted between page 1 and page 2 shifts
    every subsequent row: the caller silently skips records or sees one twice.
    For a list of trip scenarios being generated while the user reads them, that
    is not a rare edge case — it is the normal case.

THE CURSOR IS OPAQUE, AND OPAQUE MEANS OPAQUE
    It is base64url of a JSON keyset. That is an encoding, **not** encryption, and
    this module never pretends otherwise: anything placed in a cursor is readable
    by the client.

    So a cursor carries a sort key and an identifier and nothing else. It must
    never carry a tenant ID — a client that can edit a cursor could then edit the
    tenant, and tenant context comes from the token, never from client input
    (`REQ-SEC-001`). `decode_cursor` rejects a cursor containing tenant-shaped
    keys outright rather than trusting callers to leave them out.
"""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any, Final, NamedTuple

DEFAULT_LIMIT: Final = 25
MAX_LIMIT: Final = 100

#: Keys a cursor must never contain, because the client can rewrite them.
#:
#: Checked on decode, not merely on encode. Encode-side validation protects
#: against our own mistakes; decode-side validation protects against the client's,
#: and only one of those is an attacker.
_FORBIDDEN_CURSOR_KEYS: Final[frozenset[str]] = frozenset(
    {
        "tenant",
        "tenant_id",
        "organization",
        "organization_id",
        "org",
        "org_id",
        "user",
        "user_id",
        "actor",
        "actor_id",
        "role",
        "roles",
        "scope",
        "scopes",
    }
)


class CursorError(ValueError):
    """Raised for a malformed, oversized or unsafe cursor."""


class PageRequest(NamedTuple):
    """A validated request for one page."""

    limit: int
    keyset: dict[str, Any] | None
    """Decoded cursor position, or None for the first page."""


class Page[T](NamedTuple):
    """One page of results and the cursor for the next.

    `next_cursor` is None on the last page. There is deliberately no `total`:
    counting the full result set costs a second query on every request, and for a
    set that changes while the caller pages through it the number is stale before
    it is rendered. A caller that needs a count should ask for one explicitly.
    """

    items: list[T]
    next_cursor: str | None


def encode_cursor(keyset: dict[str, Any]) -> str:
    """Encode a keyset position as an opaque cursor."""
    _reject_unsafe(keyset, direction="encode")
    raw = json.dumps(keyset, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a cursor, refusing anything malformed or unsafe.

    Every failure mode returns the same `CursorError`. A caller cannot learn from
    the message whether their cursor was truncated, re-encoded or hand-crafted —
    which is the same reasoning as the opaque denial.
    """
    if len(cursor) > 2048:
        # A cursor is a sort key and an identifier. Anything larger is either a
        # bug or an attempt to make the server parse something expensive.
        raise CursorError("invalid cursor")
    padded = cursor + "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        value = json.loads(raw)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise CursorError("invalid cursor") from exc

    if not isinstance(value, dict):
        raise CursorError("invalid cursor")
    _reject_unsafe(value, direction="decode")
    return value


def _reject_unsafe(keyset: dict[str, Any], *, direction: str) -> None:
    for key in keyset:
        if str(key).lower() in _FORBIDDEN_CURSOR_KEYS:
            raise CursorError(
                f"cursor may not carry {key!r} ({direction}). A cursor is base64, "
                f"not encryption — the client can read and rewrite it. Tenant and "
                f"identity come from the token (REQ-SEC-001), never from a cursor."
            )


def page_request(cursor: str | None, limit: int | None) -> PageRequest:
    """Validate the pagination parameters of an incoming request.

    An out-of-range limit is **clamped, not rejected**. The distinction matters:
    `limit` is a hint about response size, not a semantic input, and failing a
    request because someone asked for 500 items teaches clients to guess the cap
    instead of reading it. A malformed cursor IS rejected, because a cursor means
    a specific position and silently returning the first page instead would show
    the caller data they had already seen as if it were new.
    """
    resolved = DEFAULT_LIMIT if limit is None else max(1, min(limit, MAX_LIMIT))
    keyset = None if cursor is None else decode_cursor(cursor)
    return PageRequest(limit=resolved, keyset=keyset)


def build_page[T](items: list[T], limit: int, next_keyset: dict[str, Any] | None) -> Page[T]:
    """Assemble a page response.

    `next_keyset` is supplied by the caller because only the caller knows the sort
    key. It is ignored when the page is not full: a page shorter than the limit is
    the last page by definition, and emitting a cursor there produces one pointless
    round trip per list in the product.
    """
    complete = len(items) >= limit
    return Page(
        items=items,
        next_cursor=encode_cursor(next_keyset) if complete and next_keyset else None,
    )
