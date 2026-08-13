"""Egress allowlist and SSRF protection — STEP-005.01 (REQ-SEC-005, TST-SEC-005).

WHAT SSRF ACTUALLY IS HERE
    This product fetches data from providers named in configuration. The classic
    attack is not "an attacker calls our API" — it is "an attacker influences a URL
    we fetch", and the most valuable target is not the public internet. It is
    169.254.169.254, the cloud instance-metadata endpoint, which hands out
    credentials to anything that can make a plain HTTP GET from inside the VPC.

    `DEC-007` has not chosen a cloud provider, and it does not matter: AWS, GCP and
    Azure all expose metadata on that address or on fd00:ec2::254.

WHY HOSTNAME ALLOWLISTING ALONE IS NOT ENOUGH
    Three ways a hostname check passes and the connection still goes somewhere else:

      1. DNS REBINDING. `evil.example` resolves to a public IP when validated and
         to 169.254.169.254 when connected. The check and the connection are two
         separate resolutions, and an attacker controls the gap.
      2. REDIRECTS. An allowlisted host answers 302 to a private address. The
         allowlist was consulted once, for the first URL.
      3. A HOST THAT SIMPLY RESOLVES INWARD. Nothing hostile required — a provider
         with a misconfigured record, or a CNAME to an internal load balancer.

    So this module validates **the resolved address**, not the name, and it is
    designed to be applied again on every redirect hop rather than once per call.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
    It does not make requests. It answers "may I connect to this?" and nothing
    else, so it can be tested exhaustively without a network and reused by any
    transport. `HttpConnector` is what enforces that the answer is consulted.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

#: Schemes we will ever fetch. Everything else is refused by name rather than by
#: omission, because `file://`, `gopher://` and `ftp://` are SSRF classics and a
#: default-deny that nobody can see is a default-deny nobody maintains.
ALLOWED_SCHEMES = frozenset({"https"})

#: Networks that must never be reached from a connector, whatever DNS says.
#:
#: Listed explicitly rather than relying on `ip.is_private`, because the standard
#: library's predicates do not agree with the threat model at every edge:
#: `is_private` covers RFC 1918 but the interesting target here is link-local, and
#: IPv4-mapped IPv6 (`::ffff:169.254.169.254`) is neither private nor link-local by
#: those predicates while resolving to exactly the address we are blocking.
_BLOCKED_V4 = tuple(
    ipaddress.ip_network(cidr)
    for cidr in (
        "0.0.0.0/8",
        "10.0.0.0/8",  # RFC 1918
        "100.64.0.0/10",  # carrier-grade NAT
        "127.0.0.0/8",  # loopback
        "169.254.0.0/16",  # link-local — CLOUD METADATA LIVES HERE
        "172.16.0.0/12",  # RFC 1918
        "192.0.0.0/24",  # IETF protocol assignments
        "192.168.0.0/16",  # RFC 1918
        "198.18.0.0/15",  # benchmarking
        "224.0.0.0/4",  # multicast
        "240.0.0.0/4",  # reserved
        "255.255.255.255/32",
    )
)

_BLOCKED_V6 = tuple(
    ipaddress.ip_network(cidr)
    for cidr in (
        "::/128",  # unspecified
        "::1/128",  # loopback
        "fc00::/7",  # unique local
        "fe80::/10",  # link-local
        "ff00::/8",  # multicast
        "fd00:ec2::254/128",  # AWS IMDS over IPv6
    )
)


class EgressDeniedError(Exception):
    """A connection was refused before it was attempted.

    Deliberately not a subclass of any HTTP error. An egress denial is a policy
    decision about our own configuration or a possible attack — not a provider
    being unavailable — and a caller that retries it is doing the wrong thing.
    """


@dataclass(frozen=True, slots=True)
class EgressPolicy:
    """Which hosts a connector may reach.

    `allowed_hosts` is exact-match, lowercase, no wildcards. A wildcard allowlist
    (`*.example.com`) is one CNAME away from being someone else's subdomain, and
    the number of providers here is small enough to enumerate.
    """

    allowed_hosts: frozenset[str]

    def __post_init__(self) -> None:
        for host in self.allowed_hosts:
            if host != host.lower().strip():
                raise ValueError(f"allowlist entries must be lowercase and trimmed: {host!r}")
            if "*" in host:
                raise ValueError(
                    f"wildcard allowlist entry {host!r} is refused. A wildcard is one "
                    f"CNAME away from being someone else's subdomain; enumerate the hosts."
                )


def is_blocked_address(address: str) -> bool:
    """True when this IP must never be connected to.

    Handles the IPv4-mapped IPv6 case explicitly — `::ffff:169.254.169.254` is the
    metadata endpoint wearing a different hat, and a naive check against the IPv6
    block list alone would pass it.
    """
    ip = ipaddress.ip_address(address)

    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    networks = _BLOCKED_V4 if isinstance(ip, ipaddress.IPv4Address) else _BLOCKED_V6
    return any(ip in network for network in networks)


def resolve(host: str) -> list[str]:
    """Every address a host resolves to.

    **All of them**, not the first. A host with one public and one private A record
    would otherwise pass or fail depending on resolver ordering — a check that is
    right most of the time and silently wrong the rest, which is worse than one
    that is consistently wrong.
    """
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise EgressDeniedError(f"cannot resolve {host!r}: {exc}") from exc
    return sorted({str(info[4][0]) for info in infos})


def check_url(url: str, policy: EgressPolicy, *, resolver: object = None) -> str:
    """Refuse or permit a URL. Returns the host on success.

    Applied to **every hop**, including redirects — see the module docstring. The
    caller passes each redirect target back through here rather than trusting that
    the first check covered the journey.

    `resolver` exists so tests can supply hostile DNS answers without a network.
    Production passes nothing and gets `resolve`.
    """
    parts = urlsplit(url)

    if parts.scheme not in ALLOWED_SCHEMES:
        raise EgressDeniedError(
            f"scheme {parts.scheme!r} is not permitted (allowed: {sorted(ALLOWED_SCHEMES)}). "
            f"Plain HTTP is refused because a provider fetched over HTTP can be "
            f"rewritten in transit, and the evidence pack would record the result as fact."
        )

    host = (parts.hostname or "").lower()
    if not host:
        raise EgressDeniedError(f"no host in URL {url!r}")

    if host not in policy.allowed_hosts:
        raise EgressDeniedError(
            f"host {host!r} is not on the egress allowlist. "
            f"Add it to the connector's policy deliberately — this is the control "
            f"that stops a redirect or a config mistake reaching an arbitrary address."
        )

    lookup = resolver if callable(resolver) else resolve
    addresses = lookup(host)
    if not addresses:
        raise EgressDeniedError(f"{host!r} resolved to nothing")

    for address in addresses:
        if is_blocked_address(address):
            raise EgressDeniedError(
                f"{host!r} resolves to {address}, which is in a blocked range. "
                f"If this is 169.254.169.254 or fd00:ec2::254 it is the cloud "
                f"instance-metadata endpoint, and a connector reaching it would be "
                f"handing out credentials. Treat this as an incident, not a config bug."
            )

    return host
