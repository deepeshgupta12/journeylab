"""Connector framework — TST-SEC-005, TST-DATA-002, TST-DATA-003 · STEP-005.01.

WHAT THESE ARE FOR
    Every one of these controls is the kind that is present in the code and absent
    in effect: an allowlist consulted once, a breaker that returns cached data, a
    validator that coerces, a checkpoint that advances too early. So the assertions
    are about the property, not the presence — a redirect must be re-checked, an
    open breaker must raise rather than return, a validator must return the SAME
    OBJECT, a checkpoint must refuse to advance past unhandled work.
"""

from __future__ import annotations

import random
from collections.abc import Callable

import httpx
import pytest
from framework import egress
from framework.checkpoint import (
    CheckpointError,
    InMemoryCheckpointStore,
    ResumableRun,
)
from framework.connector import ConnectorConfig, ConnectorError, HttpConnector
from framework.credentials import CredentialError, RotatingCredential, Secret
from framework.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    Quota,
    QuotaExhaustedError,
    RateLimitedError,
    TokenBucket,
    backoff_delay,
)
from framework.schema_gate import SchemaDriftError, SchemaRejectedError, validate

POLICY = egress.EgressPolicy(allowed_hosts=frozenset({"api.opentransportdata.swiss"}))


def resolving_to(*addresses: str) -> Callable[[str], list[str]]:
    """A fake resolver, so hostile DNS can be tested without a network."""
    return lambda host: list(addresses)


# --- TST-SEC-005: egress and SSRF --------------------------------------------


class TestEgressAllowlist:
    def test_an_allowlisted_public_host_is_permitted(self) -> None:
        assert (
            egress.check_url(
                "https://api.opentransportdata.swiss/gtfs",
                POLICY,
                resolver=resolving_to("185.35.9.1"),
            )
            == "api.opentransportdata.swiss"
        )

    def test_a_host_not_on_the_allowlist_is_refused(self) -> None:
        with pytest.raises(egress.EgressDeniedError, match="not on the egress allowlist"):
            egress.check_url("https://evil.example/x", POLICY, resolver=resolving_to("1.1.1.1"))

    def test_plain_http_is_refused(self) -> None:
        """A provider fetched over HTTP can be rewritten in transit, and the
        evidence pack would record the result as a sourced fact."""
        with pytest.raises(egress.EgressDeniedError, match="scheme"):
            egress.check_url(
                "http://api.opentransportdata.swiss/x", POLICY, resolver=resolving_to("1.1.1.1")
            )

    @pytest.mark.parametrize("scheme", ["file", "ftp", "gopher", "data"])
    def test_non_http_schemes_are_refused(self, scheme: str) -> None:
        with pytest.raises(egress.EgressDeniedError):
            egress.check_url(f"{scheme}://api.opentransportdata.swiss/x", POLICY)

    def test_a_wildcard_allowlist_entry_is_refused_at_construction(self) -> None:
        """One CNAME away from being someone else's subdomain."""
        with pytest.raises(ValueError, match="wildcard"):
            egress.EgressPolicy(allowed_hosts=frozenset({"*.example.com"}))


class TestSsrf:
    """The allowlisted host resolving somewhere it should not.

    Every case here PASSES the hostname check. That is the point: hostname
    allowlisting alone does not stop any of them.
    """

    @pytest.mark.parametrize(
        ("address", "what"),
        [
            ("169.254.169.254", "AWS/GCP/Azure instance metadata"),
            ("127.0.0.1", "loopback"),
            ("10.0.0.5", "RFC 1918"),
            ("172.16.4.4", "RFC 1918"),
            ("192.168.1.1", "RFC 1918"),
            ("0.0.0.0", "this host"),
            ("100.64.0.1", "carrier-grade NAT"),
        ],
    )
    def test_an_allowlisted_host_resolving_inward_is_refused(self, address: str, what: str) -> None:
        with pytest.raises(egress.EgressDeniedError, match="blocked range"):
            egress.check_url(
                "https://api.opentransportdata.swiss/x",
                POLICY,
                resolver=resolving_to(address),
            )

    @pytest.mark.parametrize("address", ["::1", "fe80::1", "fc00::1", "fd00:ec2::254"])
    def test_ipv6_private_and_metadata_ranges_are_refused(self, address: str) -> None:
        with pytest.raises(egress.EgressDeniedError, match="blocked range"):
            egress.check_url(
                "https://api.opentransportdata.swiss/x", POLICY, resolver=resolving_to(address)
            )

    def test_ipv4_mapped_ipv6_metadata_is_refused(self) -> None:
        """`::ffff:169.254.169.254` is the metadata endpoint wearing a different hat.

        Neither `is_private` nor `is_link_local` is True for it as an IPv6 address,
        so a check that trusts those predicates lets it through.
        """
        assert egress.is_blocked_address("::ffff:169.254.169.254")
        with pytest.raises(egress.EgressDeniedError, match="blocked range"):
            egress.check_url(
                "https://api.opentransportdata.swiss/x",
                POLICY,
                resolver=resolving_to("::ffff:169.254.169.254"),
            )

    def test_every_resolved_address_is_checked_not_just_the_first(self) -> None:
        """A host with one public and one private record must be refused.

        Checking only the first makes the outcome depend on resolver ordering —
        right most of the time and silently wrong the rest, which is worse than
        consistently wrong because it cannot be reproduced.
        """
        with pytest.raises(egress.EgressDeniedError, match="blocked range"):
            egress.check_url(
                "https://api.opentransportdata.swiss/x",
                POLICY,
                resolver=resolving_to("185.35.9.1", "169.254.169.254"),
            )

    def test_a_public_address_is_not_blocked(self) -> None:
        """Guards the guard: a blocklist that refuses everything would pass every
        test above while making the product unable to fetch anything."""
        assert not egress.is_blocked_address("185.35.9.1")
        assert not egress.is_blocked_address("2001:4860:4860::8888")


# --- TST-DATA-003: circuit breaker -------------------------------------------


class TestCircuitBreaker:
    def test_it_opens_after_the_threshold_and_refuses(self) -> None:
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        for _ in range(3):
            breaker.before_call(0.0)
            breaker.record_failure(0.0)
        assert breaker.state is CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            breaker.before_call(1.0)

    def test_an_open_breaker_returns_no_data(self) -> None:
        """REQ-DATA-003's second clause: no silent degradation to unmarked stale data.

        Asserted as a property of the TYPE — `before_call` returns None or raises,
        so there is no channel through which a cached value could be handed back.
        A breaker that could return one would be a breaker that degrades silently.
        """
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.before_call(0.0)
        breaker.record_failure(0.0)
        with pytest.raises(CircuitOpenError) as caught:
            breaker.before_call(0.5)
        assert not hasattr(caught.value, "cached")
        assert "No cached value" in str(caught.value)

    def test_it_half_opens_after_the_cooldown(self) -> None:
        breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10)
        breaker.before_call(0.0)
        breaker.record_failure(0.0)
        breaker.before_call(10.0)
        assert breaker.state is CircuitState.HALF_OPEN

    def test_half_open_admits_exactly_one_probe(self) -> None:
        """The thundering herd. Reopening fully sends the backlog at a provider
        that has just come back and knocks it down again."""
        breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10)
        breaker.before_call(0.0)
        breaker.record_failure(0.0)
        breaker.before_call(10.0)  # the probe
        with pytest.raises(CircuitOpenError, match="probe is already in flight"):
            breaker.before_call(10.1)

    def test_a_successful_probe_closes_the_circuit(self) -> None:
        breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10)
        breaker.before_call(0.0)
        breaker.record_failure(0.0)
        breaker.before_call(10.0)
        breaker.record_success()
        assert breaker.state is CircuitState.CLOSED
        breaker.before_call(10.1)  # no raise

    def test_a_failed_probe_reopens_immediately(self) -> None:
        """Not 'counts one toward the threshold again' — the provider is still
        down, and counting would send four more calls at it."""
        breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=10)
        for _ in range(5):
            breaker.before_call(0.0)
            breaker.record_failure(0.0)
        breaker.before_call(10.0)
        breaker.record_failure(10.0)
        assert breaker.state is CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            breaker.before_call(10.1)

    def test_success_resets_the_failure_count(self) -> None:
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.before_call(0.0)
        breaker.record_failure(0.0)
        breaker.record_success()
        breaker.before_call(1.0)
        breaker.record_failure(1.0)
        assert breaker.state is CircuitState.CLOSED


# --- rate limiting and quota --------------------------------------------------


class TestRateLimiting:
    def test_a_burst_is_allowed_up_to_capacity_then_refused(self) -> None:
        bucket = TokenBucket(capacity=3, refill_per_second=1)
        for _ in range(3):
            bucket.take(0.0)
        with pytest.raises(RateLimitedError):
            bucket.take(0.0)

    def test_tokens_refill_over_time(self) -> None:
        bucket = TokenBucket(capacity=2, refill_per_second=1)
        bucket.take(0.0)
        bucket.take(0.0)
        with pytest.raises(RateLimitedError):
            bucket.take(0.0)
        bucket.take(1.0)  # one second, one token

    def test_refill_never_exceeds_capacity(self) -> None:
        """Otherwise an idle connector accumulates an unbounded burst and hits the
        provider with a thousand requests the moment it wakes."""
        bucket = TokenBucket(capacity=2, refill_per_second=1)
        bucket.take(0.0)
        bucket.take(1000.0)
        bucket.take(1000.0)
        with pytest.raises(RateLimitedError):
            bucket.take(1000.0)

    def test_quota_is_a_separate_error_from_rate_limiting(self) -> None:
        """The remedies differ: a rate limit clears in seconds, a quota at the
        window boundary. Collapsing them makes a connector retry for hours."""
        quota = Quota(limit=2, window_seconds=3600)
        quota.consume(0.0)
        quota.consume(0.0)
        with pytest.raises(QuotaExhaustedError):
            quota.consume(0.0)
        assert not issubclass(QuotaExhaustedError, RateLimitedError)

    def test_quota_resets_at_the_window_boundary(self) -> None:
        quota = Quota(limit=1, window_seconds=60)
        quota.consume(0.0)
        with pytest.raises(QuotaExhaustedError):
            quota.consume(30.0)
        quota.consume(61.0)


class TestBackoff:
    def test_it_is_capped(self) -> None:
        rng = random.Random(0)
        assert all(
            backoff_delay(n, base_seconds=0.5, cap_seconds=30, rng=rng) <= 30.0
            for n in range(1, 40)
        )

    def test_full_jitter_can_return_near_zero(self) -> None:
        """Partial jitter leaves every client retrying in the same narrow band, so
        a provider that dropped a thousand requests receives them again together."""
        rng = random.Random(1)
        samples = [backoff_delay(8, rng=rng) for _ in range(200)]
        assert min(samples) < 1.0
        assert max(samples) > 10.0

    def test_attempt_is_one_based(self) -> None:
        with pytest.raises(ValueError):
            backoff_delay(0)


# --- REQ-DATA-002: schema gate ------------------------------------------------

SCHEMA = {
    "type": "object",
    "required": ["stop_id", "departure"],
    "properties": {"stop_id": {"type": "string"}, "departure": {"type": "string"}},
}


class TestSchemaGate:
    def test_a_valid_payload_is_returned_unchanged_and_identical(self) -> None:
        """Identity, not equality. A function that validates and returns a COPY is
        one refactor away from validating and returning something adjusted, and the
        signature would not change."""
        payload = {"stop_id": "8503000", "departure": "2026-08-13T09:00:00Z"}
        assert validate(payload, SCHEMA, provider="swiss") is payload

    def test_a_string_where_a_number_belongs_is_rejected_not_coerced(self) -> None:
        schema = {"type": "object", "properties": {"delay": {"type": "integer"}}}
        with pytest.raises(SchemaRejectedError, match="NOT coerced"):
            validate({"delay": "42"}, schema, provider="swiss")

    def test_a_missing_required_field_is_rejected(self) -> None:
        with pytest.raises(SchemaRejectedError):
            validate({"stop_id": "8503000"}, SCHEMA, provider="swiss")

    def test_a_top_level_type_change_is_reported_as_drift(self) -> None:
        """A provider redesign is not a skippable row — REQ-DATA-002 wants an alert."""
        with pytest.raises(SchemaDriftError):
            validate([], SCHEMA, provider="swiss")

    def test_drift_is_catchable_as_a_plain_rejection(self) -> None:
        """So a caller that only cares 'this failed' needs no change."""
        assert issubclass(SchemaDriftError, SchemaRejectedError)


# --- TST-DATA-002: checkpoints ------------------------------------------------


class TestCheckpoints:
    def test_a_fresh_run_starts_from_the_beginning(self) -> None:
        run = ResumableRun(InMemoryCheckpointStore(), "swiss")
        assert run.cursor == ""
        assert not run.resumed

    def test_a_run_resumes_where_it_stopped(self) -> None:
        store = InMemoryCheckpointStore()
        first = ResumableRun(store, "swiss")
        first.commit_batch(next_cursor="page-2", handled=100)

        second = ResumableRun(store, "swiss")
        assert second.resumed
        assert second.cursor == "page-2"
        assert second.records_seen == 100

    def test_resuming_does_not_replay_committed_batches(self) -> None:
        """The property TST-DATA-002 actually asks for. A resume that restarts from
        the beginning duplicates every record, and in an evidence pack a duplicated
        departure is a second sailing the solver will plan around."""
        store = InMemoryCheckpointStore()
        run = ResumableRun(store, "swiss")
        run.commit_batch(next_cursor="page-2", handled=50)
        run.commit_batch(next_cursor="page-3", handled=50)

        resumed = ResumableRun(store, "swiss")
        assert resumed.cursor == "page-3"
        assert resumed.records_seen == 100

    def test_an_empty_cursor_cannot_be_committed(self) -> None:
        """An empty cursor means 'start from the beginning', so committing one
        would silently restart the next run instead of resuming it."""
        run = ResumableRun(InMemoryCheckpointStore(), "swiss")
        with pytest.raises(CheckpointError, match="empty cursor"):
            run.commit_batch(next_cursor="", handled=10)

    def test_a_crash_before_commit_re_delivers_rather_than_loses(self) -> None:
        """At-least-once, deliberately. The alternative ordering — advance first,
        then handle — turns a crash into silent data loss, which is worse because
        nothing reports it."""
        store = InMemoryCheckpointStore()
        run = ResumableRun(store, "swiss")
        run.commit_batch(next_cursor="page-2", handled=50)
        # ... fetches page-2, handles nothing, process dies before commit_batch ...
        after_crash = ResumableRun(store, "swiss")
        assert after_crash.cursor == "page-2", "the uncommitted batch must be re-fetched"

    def test_checkpoints_are_per_provider(self) -> None:
        store = InMemoryCheckpointStore()
        ResumableRun(store, "swiss").commit_batch(next_cursor="s-2", handled=1)
        assert ResumableRun(store, "meteoswiss").cursor == ""


# --- credentials --------------------------------------------------------------


class _Source:
    def __init__(self, *values: str) -> None:
        self._values = list(values)
        self.calls = 0

    def fetch(self, name: str) -> str:
        self.calls += 1
        return self._values[min(self.calls - 1, len(self._values) - 1)]


class TestCredentials:
    def test_a_secret_never_renders_itself(self) -> None:
        """The commonest way a credential reaches a log is an f-string in an error
        path written by someone debugging something else."""
        secret = Secret("super-secret-token")
        assert "super-secret-token" not in str(secret)
        assert "super-secret-token" not in repr(secret)
        assert "super-secret-token" not in f"{secret}"
        assert "super-secret-token" not in f"{secret!r}"
        assert secret.reveal() == "super-secret-token"

    def test_an_empty_secret_is_refused(self) -> None:
        with pytest.raises(CredentialError):
            Secret("")

    def test_it_is_cached_within_the_ttl(self) -> None:
        source = _Source("v1")
        cred = RotatingCredential(name="swiss", source=source, ttl_seconds=300)
        cred.get(0.0)
        cred.get(299.0)
        assert source.calls == 1

    def test_it_refetches_after_the_ttl(self) -> None:
        """A credential read once and held forever survives rotation, and the
        symptom is 401s an hour after a rotation nobody connected to the outage."""
        source = _Source("v1", "v2")
        cred = RotatingCredential(name="swiss", source=source, ttl_seconds=300)
        assert cred.get(0.0).reveal() == "v1"
        assert cred.get(301.0).reveal() == "v2"

    def test_invalidate_forces_an_immediate_refetch(self) -> None:
        """Called on a 401, so a mid-TTL rotation is picked up on the retry rather
        than after an outage as long as the TTL."""
        source = _Source("v1", "v2")
        cred = RotatingCredential(name="swiss", source=source, ttl_seconds=300)
        cred.get(0.0)
        cred.invalidate()
        assert cred.get(1.0).reveal() == "v2"

    def test_a_source_failure_is_wrapped_not_swallowed(self) -> None:
        class Broken:
            def fetch(self, name: str) -> str:
                raise RuntimeError("vault unreachable")

        cred = RotatingCredential(name="swiss", source=Broken())
        with pytest.raises(CredentialError, match="vault unreachable"):
            cred.get(0.0)


# --- the composed connector ---------------------------------------------------


class _FakeTransport:
    """Records every URL actually requested, so redirect handling is observable."""

    def __init__(self, *responses: tuple[int, dict[str, str]]) -> None:
        self._responses = list(responses)
        self.requested: list[str] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requested.append(str(request.url))
        status, headers = self._responses[min(len(self.requested) - 1, len(self._responses) - 1)]
        return httpx.Response(status, headers=headers, json={"ok": True})


def _connector(
    transport_responses: list[tuple[int, dict[str, str]]],
    *,
    hosts: tuple[str, ...] = ("api.opentransportdata.swiss",),
    clock: Callable[[], float] | None = None,
) -> tuple[HttpConnector, _FakeTransport]:

    fake = _FakeTransport(*transport_responses)
    client = httpx.Client(transport=httpx.MockTransport(fake.handle), follow_redirects=False)
    connector = HttpConnector(
        ConnectorConfig(
            provider="swiss", policy=egress.EgressPolicy(allowed_hosts=frozenset(hosts))
        ),
        bucket=TokenBucket(capacity=10, refill_per_second=10),
        quota=Quota(limit=100, window_seconds=3600),
        client=client,
        clock=clock or (lambda: 0.0),
    )
    return connector, fake


class TestConnectorAppliesEveryControl:
    def test_a_normal_fetch_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(egress, "resolve", lambda host: ["185.35.9.1"])
        connector, fake = _connector([(200, {})])
        response = connector.get("https://api.opentransportdata.swiss/gtfs")
        assert response.status_code == 200
        assert fake.requested == ["https://api.opentransportdata.swiss/gtfs"]

    def test_a_redirect_to_a_blocked_address_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE BYPASS THIS FRAMEWORK EXISTS FOR.

        An allowlisted host answers 302 to the cloud metadata endpoint. `httpx`
        would follow it happily, and the allowlist was consulted once — for the
        first URL. The second hop must be checked too.
        """
        resolutions = {
            "api.opentransportdata.swiss": ["185.35.9.1"],
            "metadata.internal": ["169.254.169.254"],
        }
        monkeypatch.setattr(egress, "resolve", lambda host: resolutions[host])
        connector, fake = _connector(
            [(302, {"location": "https://metadata.internal/latest/meta-data/"})]
        )
        with pytest.raises(egress.EgressDeniedError):
            connector.get("https://api.opentransportdata.swiss/gtfs")
        # It was refused BEFORE the second request went out.
        assert len(fake.requested) == 1

    def test_a_redirect_to_a_non_allowlisted_host_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(egress, "resolve", lambda host: ["185.35.9.1"])
        connector, fake = _connector([(302, {"location": "https://elsewhere.example/x"})])
        with pytest.raises(egress.EgressDeniedError, match="not on the egress allowlist"):
            connector.get("https://api.opentransportdata.swiss/gtfs")
        assert len(fake.requested) == 1

    def test_an_egress_denial_does_not_trip_the_breaker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Our policy or an attack — not the provider being unhealthy. Counting it
        would let one bad config trip the circuit for a provider that is fine."""
        monkeypatch.setattr(egress, "resolve", lambda host: ["185.35.9.1"])
        connector, _ = _connector([(302, {"location": "https://elsewhere.example/x"})])
        with pytest.raises(egress.EgressDeniedError):
            connector.get("https://api.opentransportdata.swiss/gtfs")
        assert connector.breaker.consecutive_failures == 0
        assert connector.breaker.state is CircuitState.CLOSED

    def test_a_5xx_does_trip_the_breaker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(egress, "resolve", lambda host: ["185.35.9.1"])
        connector, _ = _connector([(503, {})])
        with pytest.raises(ConnectorError):
            connector.get("https://api.opentransportdata.swiss/gtfs")
        assert connector.breaker.consecutive_failures == 1

    def test_a_redirect_loop_terminates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(egress, "resolve", lambda host: ["185.35.9.1"])
        connector, _ = _connector([(302, {"location": "https://api.opentransportdata.swiss/loop"})])
        with pytest.raises(ConnectorError, match="redirects"):
            connector.get("https://api.opentransportdata.swiss/gtfs")

    def test_an_unbounded_timeout_cannot_be_configured(self) -> None:
        from framework.connector import ConnectorConfig

        with pytest.raises(ValueError, match="positive"):
            ConnectorConfig(
                provider="swiss",
                policy=egress.EgressPolicy(allowed_hosts=frozenset({"a.example"})),
                timeout_seconds=0,
            )

    def test_the_production_client_does_not_follow_redirects_itself(self) -> None:
        """A GAP FOUND BY MUTATION TESTING, not by writing more cases.

        Every other test here injects a client, so the constructor's own
        `follow_redirects=False` was never exercised. Flipping it to True left the
        entire suite green — and it is not cosmetic: httpx would follow the
        redirect internally and return the FINAL response, so hop two would never
        reach `egress.check_url` and the metadata-endpoint bypass would be open
        again with every redirect test still passing.

        White-box, deliberately. The behaviour being protected is a constructor
        default, and there is nowhere else to observe it.
        """
        connector = HttpConnector(
            ConnectorConfig(
                provider="swiss",
                policy=egress.EgressPolicy(allowed_hosts=frozenset({"a.example"})),
            ),
            bucket=TokenBucket(capacity=1, refill_per_second=1),
            quota=Quota(limit=1, window_seconds=1),
        )
        try:
            assert connector._client.follow_redirects is False, (
                "the framework must follow redirects manually so every hop is "
                "re-checked against the egress policy"
            )
            assert connector._client.timeout.read == 10.0
        finally:
            connector.close()
