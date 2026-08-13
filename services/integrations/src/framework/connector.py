"""The one way to make an outbound call — STEP-005.01 (REQ-SEC-005, REQ-DATA-002/003).

WHY EVERYTHING IS COMPOSED HERE INSTEAD OF OFFERED AS UTILITIES
    The sub-step's outcome is "no adapter reimplements resilience". A library of
    helpers does not achieve that — it achieves "no adapter *has to*", which is a
    different and much weaker claim. The next adapter under deadline reaches for
    `httpx` directly and every control is silently absent.

    So `HttpConnector` owns the client, and an adapter is handed a connector rather
    than a URL. The controls are not applied by convention; there is no path that
    skips them.

ORDER OF CHECKS, AND WHY IT IS THIS ORDER
    1. **Circuit breaker** — cheapest, and a provider we have given up on should not
       consume a rate-limit token.
    2. **Quota**, then **rate limit** — a call that cannot happen today should not
       burn a token that clears in a second.
    3. **Egress** — the security control. Last among the pre-flight checks because
       it may perform DNS, and doing that for a call we were going to refuse anyway
       wastes a resolution and leaks a lookup for a host we never contact.

    A denial from any of them is raised, never swallowed and never substituted with
    cached data (`REQ-DATA-003`).

REDIRECTS ARE FOLLOWED MANUALLY, AND THAT IS THE POINT
    `httpx` will follow redirects for us and the allowlist would then have been
    consulted exactly once, for the first URL. An allowlisted host answering 302 to
    169.254.169.254 is the textbook bypass. Every hop goes back through
    `egress.check_url`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from . import egress
from .credentials import RotatingCredential
from .resilience import CircuitBreaker, Quota, TokenBucket

#: No request may be unbounded. `httpx`'s default is 5s connect but no overall
#: read cap in some configurations, and a provider that accepts a connection then
#: never answers would hold an ingestion run open indefinitely.
DEFAULT_TIMEOUT_SECONDS = 10.0

#: A redirect chain longer than this is a loop or an attempt to exhaust the check.
MAX_REDIRECTS = 3


class ConnectorError(Exception):
    """A call failed after the framework's controls were applied."""


@dataclass(slots=True)
class ConnectorConfig:
    provider: str
    policy: egress.EgressPolicy
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive — there is deliberately no way to "
                "configure an unbounded request (REQ-SEC-005)"
            )


class HttpConnector:
    """An outbound HTTP client with every REQ-SEC-005 control attached."""

    def __init__(
        self,
        config: ConnectorConfig,
        *,
        bucket: TokenBucket,
        quota: Quota,
        breaker: CircuitBreaker | None = None,
        credential: RotatingCredential | None = None,
        client: httpx.Client | None = None,
        clock: Any = time.monotonic,
    ) -> None:
        self._config = config
        self._bucket = bucket
        self._quota = quota
        self._breaker = breaker or CircuitBreaker()
        self._credential = credential
        self._clock = clock
        # follow_redirects=False is load-bearing, not a default we inherited.
        self._client = client or httpx.Client(
            timeout=config.timeout_seconds, follow_redirects=False
        )

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    def get(self, url: str, *, headers: dict[str, str] | None = None) -> httpx.Response:
        """Fetch a URL with all controls applied. Raises rather than degrading."""
        now = self._clock()

        self._breaker.before_call(now)
        self._quota.consume(now)
        self._bucket.take(now)

        request_headers = dict(headers or {})
        if self._credential is not None:
            request_headers["Authorization"] = f"Bearer {self._credential.get(now).reveal()}"

        current = url
        try:
            for _ in range(MAX_REDIRECTS + 1):
                # EVERY hop, including redirects. See the module docstring.
                egress.check_url(current, self._config.policy)
                response = self._client.get(current, headers=request_headers)

                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        raise ConnectorError(
                            f"{self._config.provider}: redirect with no Location header"
                        )
                    current = str(httpx.URL(current).join(location))
                    continue

                if response.status_code == 401 and self._credential is not None:
                    # A rotation may have happened inside the TTL. Drop the cache so
                    # the next attempt re-fetches instead of failing for the whole TTL.
                    self._credential.invalidate()

                if response.status_code >= 500:
                    raise ConnectorError(
                        f"{self._config.provider}: upstream returned {response.status_code}"
                    )

                self._breaker.record_success()
                return response

            raise ConnectorError(f"{self._config.provider}: more than {MAX_REDIRECTS} redirects")
        except egress.EgressDeniedError:
            # NOT a provider failure. An egress denial is our policy or an attack,
            # and counting it toward the breaker would let a misconfigured host
            # trip the circuit for a provider that is perfectly healthy.
            raise
        except Exception:
            self._breaker.record_failure(self._clock())
            raise

    def close(self) -> None:
        self._client.close()
