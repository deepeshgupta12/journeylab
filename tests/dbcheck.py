"""One decision about whether the database is available — STEP-001.07.

WHY THIS EXISTS, AND WHY IT IS NOT JUST TIDYING
    Five test modules each defined their own `_stack_up()` and their own
    `requires_db` marker. The knowledge graph found all five when asked for the
    blast radius of changing one (`BR-037` §2).

    Five copies is not primarily a duplication problem. It meant the decision
    "skip these tests" was being taken forty-one times, in five places, with
    nothing able to change it centrally — which is why nobody noticed that CI had
    been taking it on every push since STEP-002.01. `BUG-023`.

THE RATCHET
    A skip is the right behaviour on a laptop with no stack running. It is the
    wrong behaviour in CI, where the database is supposed to be there: a service
    container that fails to start, gets renamed, or moves port would send
    forty-one tests back to skipping under a green build — the exact failure this
    sub-step exists to close, silently restored.

    So an environment that expects a database says so:

        JOURNEYLAB_REQUIRE_DB=1

    and absence becomes an error instead of a skip. `tests/e2e/smoke.sh` has said
    "a skip is not a pass" since STEP-003; this is the first time the rule is
    enforced by something other than a human reading the output.
"""

from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

import pytest

#: The same default the dev stack publishes (docker-compose.dev.yml, port 5700).
#: Overridable so CI and the mirror can point at their own service.
#:
#: TWO NAMES, AND THAT WAS ITS OWN LATENT BUG.
#:     The suite read the database location from `JOURNEYLAB_DATABASE_URL` in one
#:     module and `JOURNEYLAB_TEST_DSN` in four others. Setting either one in CI
#:     would have pointed some modules at the service and left the rest aimed at
#:     127.0.0.1:5700 — connection failures in a subset of tests, with nothing
#:     saying why. Found while consolidating the five copies (STEP-001.07).
#:
#:     `JOURNEYLAB_TEST_DSN` is still honoured so an existing override does not
#:     silently stop working; `JOURNEYLAB_DATABASE_URL` wins because it is the
#:     name the application will use.
DSN = (
    os.environ.get("JOURNEYLAB_DATABASE_URL")
    or os.environ.get("JOURNEYLAB_TEST_DSN")
    or "postgresql://journeylab:journeylab_dev_only@127.0.0.1:5700/journeylab"
)

#: Set in CI and in `pnpm ci:local`. Any non-empty value other than "0" counts.
REQUIRE_DB = os.environ.get("JOURNEYLAB_REQUIRE_DB", "").strip() not in ("", "0")


def _host_and_port() -> tuple[str, int]:
    """Derive the TCP endpoint from the DSN rather than hardcoding it.

    The reachability probe and the connection the tests actually make must agree.
    A probe pointed at 127.0.0.1:5700 while `JOURNEYLAB_DATABASE_URL` names a
    service host would report "up" and then every test would fail to connect —
    or, worse, report "down" and skip while a perfectly good database was running.
    """
    parsed = urlparse(DSN)
    return parsed.hostname or "127.0.0.1", parsed.port or 5432


def stack_is_up(timeout_seconds: float = 2.0) -> bool:
    """True when something is accepting TCP connections at the DSN's endpoint.

    A TCP probe, not a query. It answers "is there a server here" quickly and
    without needing credentials; whether that server is a healthy PostgreSQL with
    migrations applied is what the tests themselves determine, and conflating the
    two would turn every schema error into a skip.
    """
    host, port = _host_and_port()
    with socket.socket() as probe:
        probe.settimeout(timeout_seconds)
        return probe.connect_ex((host, port)) == 0


def _reason() -> str:
    host, port = _host_and_port()
    return (
        f"no database at {host}:{port} (start it with `pnpm dev`). "
        f"Set JOURNEYLAB_REQUIRE_DB=1 to make this a failure instead of a skip."
    )


#: Apply to any test that needs PostgreSQL.
#:
#: Evaluated once at import, deliberately. Probing per test would add a TCP
#: round trip to each of forty-one tests, and a database that disappears
#: mid-suite is a broken environment rather than a condition to tolerate.
if REQUIRE_DB and not stack_is_up():
    host, port = _host_and_port()
    raise RuntimeError(
        f"JOURNEYLAB_REQUIRE_DB is set but no database is reachable at {host}:{port}.\n"
        f"\n"
        f"This is deliberate and it is not a flake. The flag means 'a database is\n"
        f"expected here', so its absence is a build failure rather than forty-one\n"
        f"silently skipped tests — which is what CI did on every push from\n"
        f"STEP-002.01 until STEP-001.07 (BUG-023).\n"
        f"\n"
        f"Either start the database, or unset JOURNEYLAB_REQUIRE_DB if this\n"
        f"environment genuinely has none."
    )

requires_db = pytest.mark.skipif(not stack_is_up(), reason=_reason())
