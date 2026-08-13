"""Rate limits, backoff and the circuit breaker — STEP-005.01 (REQ-DATA-003, TST-DATA-003).

THE REQUIREMENT IS NOT "RETRY THINGS"
    `REQ-DATA-003`: "Provider failure must trip a circuit breaker **and must not
    silently degrade to unmarked stale data**."

    The second clause is the one with teeth, and it is why `CircuitOpenError` is an
    exception rather than a cached value. The tempting behaviour when a provider is
    down is to serve the last good answer — it keeps the product responsive and it
    is exactly the failure this product exists to prevent. A ferry timetable from
    yesterday, rendered without a staleness marker, is a plausible invalid plan
    (`REQ-CONS-005`) with a citation attached.

    So this module never returns data. It either lets a call proceed or refuses,
    and the refusal is loud. Whether a stale value may be shown, and how it must be
    labelled, is an evidence-layer decision (`REQ-EVID-001`), not a transport one.

WHY THE BREAKER COUNTS CONSECUTIVE FAILURES
    A rolling error rate is the more sophisticated choice and the wrong one at this
    stage: it needs a window, a minimum sample size and a tuning exercise nobody has
    data for yet. Consecutive failures need one number, behave predictably on a
    provider that is simply down, and are trivially explainable in an incident.

    The cost is honest: a provider failing 50% of the time never trips. That is
    recorded here rather than discovered, and revisited when there is traffic to
    tune against.
"""

from __future__ import annotations

import enum
import random
from dataclasses import dataclass, field


class CircuitState(enum.StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """The breaker is open; the call was not attempted.

    Carries no data, deliberately. See the module docstring: a breaker that could
    return a cached value is a breaker that silently degrades.
    """


class RateLimitedError(Exception):
    """Our own limiter refused the call — we would have exceeded the provider's budget."""


class QuotaExhaustedError(Exception):
    """The budget for this window is spent.

    Distinct from `RateLimitedError` because the remedies differ: a rate limit clears in
    seconds and is worth waiting for, a quota clears at the window boundary and is
    a capacity decision. Collapsing them into one error makes a connector retry
    something that cannot succeed for hours.
    """


@dataclass
class TokenBucket:
    """Per-provider rate limiting.

    A token bucket rather than a fixed window: a fixed window permits a burst of
    2N across a boundary, which is precisely when a provider's own limiter sees us
    as abusive. Bursting is allowed up to `capacity` because most providers do
    tolerate it and refusing to burst wastes the allowance.

    Not thread-safe and not async-locked. Each connector owns its own bucket; if a
    connector is ever run concurrently in one process, this needs a lock, and that
    is a change nobody should make accidentally.
    """

    capacity: float
    refill_per_second: float
    tokens: float = field(init=False)
    # None, not 0.0. A sentinel that is also a legal value is a bug waiting for
    # the first caller whose clock starts at zero — which is every test that
    # injects one, and was three failures on the first run here.
    _last: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.capacity <= 0 or self.refill_per_second <= 0:
            raise ValueError("capacity and refill_per_second must be positive")
        self.tokens = self.capacity

    def take(self, now: float, amount: float = 1.0) -> None:
        """Consume one token or raise. `now` is injected so tests need no sleeping."""
        elapsed = 0.0 if self._last is None else max(0.0, now - self._last)
        self._last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)

        if self.tokens < amount:
            wait = (amount - self.tokens) / self.refill_per_second
            raise RateLimitedError(
                f"rate limit reached; {wait:.2f}s until a token is available. "
                f"This is OUR limiter, not the provider's — being refused here is how "
                f"we avoid being refused there, where the penalty may be a ban."
            )
        self.tokens -= amount


@dataclass
class Quota:
    """A hard ceiling per window, independent of rate.

    Rate limiting shapes traffic; a quota bounds cost and blast radius. A connector
    stuck in a retry loop respects the rate limit perfectly while making a hundred
    thousand calls a day, and the limiter is content because each one was spaced
    correctly.
    """

    limit: int
    window_seconds: float
    used: int = 0
    _window_start: float | None = field(default=None, init=False)

    def consume(self, now: float, amount: int = 1) -> None:
        if self._window_start is None:
            self._window_start = now
        if now - self._window_start >= self.window_seconds:
            self._window_start = now
            self.used = 0
        if self.used + amount > self.limit:
            remaining = self.window_seconds - (now - (self._window_start or now))
            raise QuotaExhaustedError(
                f"quota of {self.limit} exhausted; window resets in {remaining:.0f}s"
            )
        self.used += amount


@dataclass
class CircuitBreaker:
    """Consecutive-failure breaker with a half-open probe.

    HALF-OPEN ADMITS EXACTLY ONE CALL, and that is the whole design.
        Reopening the gates fully after a cooldown sends the entire backlog at a
        provider that has just come back, which knocks it down again — the
        thundering herd that turns a brief outage into a long one. One probe
        decides: success closes, failure reopens and restarts the cooldown.
    """

    failure_threshold: int = 5
    cooldown_seconds: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float | None = None
    _probe_in_flight: bool = field(default=False, init=False)

    def before_call(self, now: float) -> None:
        """Raise `CircuitOpenError` unless this call may proceed."""
        if self.state is CircuitState.CLOSED:
            return

        if self.state is CircuitState.OPEN:
            if self.opened_at is not None and now - self.opened_at >= self.cooldown_seconds:
                self.state = CircuitState.HALF_OPEN
                self._probe_in_flight = False
            else:
                remaining = self.cooldown_seconds - (now - (self.opened_at or now))
                raise CircuitOpenError(
                    f"circuit open for another {remaining:.0f}s after "
                    f"{self.consecutive_failures} consecutive failures. "
                    f"No cached value is returned by design (REQ-DATA-003): stale data "
                    f"without a staleness marker is a plausible invalid plan."
                )

        if self.state is CircuitState.HALF_OPEN:
            if self._probe_in_flight:
                raise CircuitOpenError(
                    "circuit is half-open and a probe is already in flight. "
                    "Exactly one call decides whether the provider is back; letting "
                    "the backlog through would knock it over again."
                )
            self._probe_in_flight = True

    def record_success(self) -> None:
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.opened_at = None
        self._probe_in_flight = False

    def record_failure(self, now: float) -> None:
        self._probe_in_flight = False
        self.consecutive_failures += 1
        # A failed half-open probe reopens immediately — the provider is still down,
        # and counting to the threshold again would send four more calls at it.
        if (
            self.state is CircuitState.HALF_OPEN
            or self.consecutive_failures >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
            self.opened_at = now


def backoff_delay(
    attempt: int,
    *,
    base_seconds: float = 0.5,
    cap_seconds: float = 30.0,
    rng: random.Random | None = None,
) -> float:
    """Capped exponential backoff with **full** jitter.

    `random.uniform(0, exponential)` rather than `exponential ± a bit`. Partial
    jitter leaves every client retrying in the same narrow band, so a provider that
    dropped a thousand requests receives them again together. Full jitter spreads
    them across the whole interval, which is the point of jittering at all.

    Capped because unbounded doubling reaches hours, and a connector that will next
    try in four hours is indistinguishable from one that has stopped.

    `rng` is injectable so a test can assert the bounds deterministically instead of
    sampling and hoping.
    """
    if attempt < 1:
        raise ValueError("attempt is 1-based")
    generator = rng or random
    exponential = min(cap_seconds, base_seconds * (2 ** (attempt - 1)))

    # here would cost entropy on every retry to defend against an attacker who
    # gains nothing from predicting when we next call a public timetable API.
    return generator.uniform(0.0, exponential)
