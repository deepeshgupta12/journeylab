"""Redaction at emission — STEP-002.07 (REQ-SEC-007).

REDACTION HAPPENS BEFORE THE WRITE, NOT AT QUERY TIME
    Redacting on read means the raw value is already durably stored, and every
    future reader — a backup, a replica, an export, an incident responder with a
    psql prompt — sees it. Redacting at emission means it was never written.

FAILURE BLOCKS EMISSION
    §8 is explicit: "Redaction failure blocks emission rather than leaking." So
    this module raises rather than returning a best-effort result. A caller that
    wants the event written must give it something redactable; there is no
    `force=True`.

    The final sweep matters most: after masking known-sensitive keys, every
    remaining value is re-checked against the secret patterns. If something still
    looks like a credential — because it arrived under an innocuous key name — the
    event is refused instead of written.
"""

from __future__ import annotations

import re
from typing import Any

MASK = "[redacted]"


class RedactionError(Exception):
    """Raised when a payload cannot be safely redacted. Blocks the write."""


# Key names whose VALUE is sensitive regardless of what it looks like.
SENSITIVE_KEYS = re.compile(
    r"(password|passwd|secret|token|credential|authorization|api_?key|private_?key"
    r"|session|cookie|otp|pin|ssn|passport|card|cvv|iban)",
    re.IGNORECASE,
)

# Values that look like credentials whatever key they arrived under.
SECRET_VALUE_PATTERNS = [
    re.compile(r"^ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."),  # JWT
    re.compile(r"^Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),  # provider-style API key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"^[A-Fa-f0-9]{40,}$"),  # long hex — hashes, raw keys
]

# PII that must not sit in an audit payload. Email is the common one: it arrives
# through provisioning and reads as harmless.
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _looks_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS)


def _redact_value(key: str, value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _redact_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    if not isinstance(value, str):
        return value

    if SENSITIVE_KEYS.search(key):
        return MASK
    if _looks_secret(value):
        return MASK
    if EMAIL.search(value):
        # Keep the domain: it is operationally useful (which identity provider,
        # which corporate tenant) and is not personally identifying on its own.
        return EMAIL.sub(lambda m: f"{MASK}@{m.group(0).split('@', 1)[1]}", value)
    return value


def _remaining_secrets(value: Any, path: str = "") -> list[str]:
    """Paths whose value still looks like a credential after redaction."""
    found: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            found += _remaining_secrets(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found += _remaining_secrets(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if value != MASK and _looks_secret(value):
            found.append(path or "<root>")
    elif value is not None and not isinstance(value, bool | int | float):
        # A type the masker does not understand — a tuple, a set, a custom object.
        # It passed through `_redact_value` unchanged, so its contents were never
        # masked. Check its string form: this is the branch that makes fail-closed
        # reachable rather than decorative, and it was found by a test proving a
        # tuple containing a private key survived redaction untouched.
        if _looks_secret(str(value)):
            found.append(f"{path or '<root>'} (unhandled type {type(value).__name__})")
    return found


def redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy, or raise and block the write.

    Raises `RedactionError` when a value still matches a secret pattern after
    masking. That is the fail-closed branch: refusing to record an event is a
    recoverable gap, whereas writing a credential into an append-only store is
    not — by design, the row cannot be deleted afterwards.
    """
    redacted = {k: _redact_value(k, v) for k, v in payload.items()}

    leftover = _remaining_secrets(redacted)
    if leftover:
        raise RedactionError(
            "refusing to emit an audit event: value(s) still look like credentials "
            f"after redaction at {leftover}. The audit store is append-only, so a "
            "leaked secret could not be deleted afterwards."
        )
    return redacted
