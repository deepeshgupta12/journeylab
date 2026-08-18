"""Deep links and what partners actually preserve — STEP-005.06 (REQ-BOOK-001).

WHY PARAMETER PRESERVATION IS RECORDED RATHER THAN ASSUMED

    §5: "Record which parameters each partner actually preserves — this validates
    `ASM-012` empirically."

    `ASM-012` assumes a deep link can carry itinerary context. Partners vary
    wildly: some preserve dates and party size, some drop everything but the
    product id, some silently substitute defaults. **A dropped parameter is worse
    than a rejected one** — the traveller lands on a page showing a different date
    for a different number of people, and nothing indicates the context was lost.

    So `PartnerLinkProfile` records what each partner is *observed* to preserve,
    with the date it was checked. Unverified is its own state, distinct from
    "does not preserve", for the same reason unknown opening hours are distinct
    from closed (`STEP-005.02`).

WHAT IS NOT PUT IN A LINK
    A deep link is a URL: it lands in browser history, in referrer headers and in
    the partner's logs. Nothing identifying goes in one. The click reference is
    opaque and ours, so an attribution can be matched later without the URL
    carrying who the traveller is.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import urlencode, urlsplit


class DeepLinkError(ValueError):
    """A deep link could not be built safely."""


class Preservation(enum.StrEnum):
    """What a partner does with a parameter, as observed."""

    PRESERVED = "preserved"
    DROPPED = "dropped"
    #: Replaced with the partner's own default — the most dangerous outcome,
    #: because the page looks correct and describes a different trip.
    SUBSTITUTED = "substituted"
    #: Never checked. NOT the same as "dropped".
    UNVERIFIED = "unverified"


@dataclass(frozen=True, slots=True)
class PartnerLinkProfile:
    """What a partner was observed to do, and when it was checked."""

    partner_id: str
    parameters: dict[str, Preservation]
    checked_at: datetime | None

    def __post_init__(self) -> None:
        if self.checked_at is None:
            if any(p is not Preservation.UNVERIFIED for p in self.parameters.values()):
                raise DeepLinkError(
                    f"{self.partner_id}: a preservation claim needs a check date. "
                    f"Undated, it is an assumption wearing an observation's clothes "
                    f"(ASM-012)."
                )
        elif self.checked_at.tzinfo is None:
            raise DeepLinkError("checked_at must be timezone-aware")

    def preserves(self, parameter: str) -> Preservation:
        return self.parameters.get(parameter, Preservation.UNVERIFIED)


@dataclass(frozen=True, slots=True)
class DeepLink:
    url: str
    click_reference: str
    #: Parameters we sent that the partner is NOT known to preserve. Surfaced so
    #: the interface can warn rather than implying the context carried over.
    unreliable_parameters: tuple[str, ...]


#: Parameters that may appear in a deep link. Anything identifying is absent by
#: construction — a URL reaches browser history, referrer headers and partner logs.
ALLOWED_PARAMETERS = frozenset({"check_in", "check_out", "party_size", "product_id", "click_ref"})


def build_deep_link(
    *,
    base_url: str,
    partner: PartnerLinkProfile,
    click_reference: str,
    check_in: date | None = None,
    check_out: date | None = None,
    party_size: int | None = None,
    product_id: str | None = None,
) -> DeepLink:
    """Build a link, reporting which parameters the partner may not honour."""
    parts = urlsplit(base_url)
    if parts.scheme != "https":
        raise DeepLinkError(
            f"deep links must be https, got {parts.scheme!r}: a booking handoff over "
            f"plain HTTP can be rewritten in transit"
        )
    if not parts.netloc:
        raise DeepLinkError("deep link needs a host")

    candidate: dict[str, str] = {"click_ref": click_reference}
    if check_in is not None:
        candidate["check_in"] = check_in.isoformat()
    if check_out is not None:
        candidate["check_out"] = check_out.isoformat()
    if party_size is not None:
        if party_size < 1:
            raise DeepLinkError("party_size must be at least 1")
        candidate["party_size"] = str(party_size)
    if product_id is not None:
        candidate["product_id"] = product_id

    unexpected = set(candidate) - ALLOWED_PARAMETERS
    if unexpected:
        raise DeepLinkError(f"parameters not on the allowlist: {sorted(unexpected)}")

    unreliable = tuple(
        sorted(
            name
            for name in candidate
            if name != "click_ref" and partner.preserves(name) is not Preservation.PRESERVED
        )
    )
    separator = "&" if parts.query else "?"
    return DeepLink(
        url=f"{base_url}{separator}{urlencode(candidate)}",
        click_reference=click_reference,
        unreliable_parameters=unreliable,
    )
