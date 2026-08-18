"""Attribution records — STEP-005.06 (REQ-BOOK-001, TST-BOOK-002).

"NO PAYMENT CREDENTIAL ANYWHERE" IS ENFORCED BY HAVING NOWHERE TO PUT ONE

    TST-BOOK-002: "No code path can persist a payment credential."

    A redaction pass cannot satisfy that, because redaction runs *after* the value
    is in memory and one forgotten call away from a log. The same argument as
    `service_identities` in migration 001, which has no secret column at all: a
    credential that cannot be stored cannot be leaked.

    So `AttributionRecord` is a closed set of fields, none of which is a card
    number, and `reject_payment_fields` refuses a partner payload that carries one
    rather than dropping it silently. Refusing is deliberate — a partner that
    starts sending card data is a contract change we must notice, not a stream to
    quietly filter.

WHAT AN ATTRIBUTION ACTUALLY NEEDS
    Whether a click became a booking, and for whom. That is a reference and an
    outcome. It never needs an instrument, and a field that is never needed is a
    field that should not exist — every optional one is a place for something to
    end up by accident.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class AttributionError(ValueError):
    """An attribution record could not be built safely."""


class BookingOutcome(enum.StrEnum):
    CLICKED = "clicked"
    BOOKED = "booked"
    CANCELLED = "cancelled"


#: Field names that must never appear in a partner payload we retain.
#:
#: Matched on the SHAPE of the name rather than an exact list, because a partner
#: naming a field `cardNumber`, `card_number` or `ccnum` is doing the same thing,
#: and an exact-match list is a list somebody has to keep complete forever.
_PAYMENT_SHAPED = re.compile(
    r"(card[_-]?(number|num|no)\b|\bcc[_-]?(num|no|number)\b|\bpan\b|cvv|cvc|security[_-]?code|"
    r"iban|sort[_-]?code|account[_-]?number|routing[_-]?number|"
    r"expir\w*[_-]?(date|month|year)|cardholder)",
    re.IGNORECASE,
)


def reject_payment_fields(payload: dict[str, Any], *, path: str = "") -> None:
    """Raise if a payload carries anything payment-shaped, at any depth.

    Refuses rather than strips. A partner that begins sending card data has changed
    the contract, and silently filtering it means nobody finds out — while the
    value has still passed through our process, our memory and possibly our logs on
    the way to being dropped.
    """
    for key, value in payload.items():
        here = f"{path}.{key}" if path else key
        if _PAYMENT_SHAPED.search(str(key)):
            raise AttributionError(
                f"payload field {here!r} is payment-shaped and this system stores no "
                f"payment data (REQ-BOOK-002). NOT stripped: a partner sending card "
                f"data is a contract change to escalate, not a stream to filter."
            )
        if isinstance(value, dict):
            reject_payment_fields(value, path=here)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    reject_payment_fields(item, path=f"{here}[{index}]")


@dataclass(frozen=True, slots=True)
class AttributionRecord:
    """That a click became a booking, and for whom.

    A closed set of fields. There is no `payment_method`, no `card_last_four`, no
    `billing_address` — not because they are redacted, but because they do not
    exist. `slots=True` means an attribute cannot even be attached at runtime.
    """

    partner_id: str
    #: Our own opaque reference for the click. Not the traveller's identity.
    click_reference: str
    #: The partner's booking reference, when there is one.
    partner_booking_reference: str | None
    outcome: BookingOutcome
    occurred_at: datetime
    tenant_id: str

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise AttributionError("occurred_at must be timezone-aware")
        if not self.tenant_id.strip():
            raise AttributionError(
                "tenant_id is required on every row (REQ-SEC-001); an attribution "
                "without one cannot be isolated or deleted"
            )
        if self.outcome is BookingOutcome.BOOKED and not self.partner_booking_reference:
            raise AttributionError(
                "a booked outcome without a partner reference cannot be reconciled "
                "or refunded, so it is not a booking we can stand behind"
            )
