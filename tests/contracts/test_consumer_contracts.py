"""Consumer-driven contract tests — STEP-004.08 (REQ-PLAT-008).

WHAT A CONSUMER-DRIVEN CONTRACT TEST IS, AND WHAT THIS ONE HONESTLY IS
    The real pattern: each consumer publishes the subset of the provider's contract
    it actually depends on, and the provider's build fails when it stops satisfying
    any of them. Its value comes entirely from the expectations being written by
    someone other than the provider — a provider guessing at its own consumers'
    needs is writing provider tests with a different name on them.

    **This repository has no external consumer.** No partner integrates, no webhook
    is delivered, and the only client is the one generated from this same contract
    in STEP-004.07. So nothing here can be a consumer-driven contract test in the
    sense that matters, and calling the file that without saying so would be the
    kind of claim this repository's logs exist to prevent.

    What it is instead: **the harness, plus the expectations of the one consumer
    that does exist**, written down in the form a real consumer would use. When a
    partner arrives in STEP-016, their expectations get added as another
    `ConsumerExpectation` and the machinery below already runs them.

WHY WRITE THE EXPECTATIONS DOWN AT ALL, GIVEN THAT WE OWN BOTH SIDES
    Because "the API contract" and "what a caller relies on" are different sets, and
    only the second one breaking actually hurts anyone. The compatibility differ in
    `tools/contract_diff.py` reports every structural change; these expectations say
    which of them a real caller would notice. A change that is technically breaking
    and touches nothing anyone reads is a different problem from one that removes a
    field the itinerary view renders.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[2]
SPEC: dict[str, Any] = yaml.safe_load((REPO / "contracts" / "openapi.yaml").read_text())


@dataclass(frozen=True)
class ConsumerExpectation:
    """One thing a named consumer depends on, and why.

    `why` is required and is not decoration. An expectation whose rationale nobody
    recorded is one nobody can ever safely delete, so it accumulates until the whole
    suite is treated as noise.
    """

    consumer: str
    operation: str
    """`METHOD path`."""
    reads: tuple[str, ...] = ()
    """Response schema names this consumer reads."""
    sends: tuple[str, ...] = ()
    """Request schema names this consumer sends."""
    why: str = ""


#: The expectations of every known consumer.
#:
#: One consumer today. The list is the point: when STEP-016 adds a partner, its
#: expectations go here and the tests below run against them unchanged.
EXPECTATIONS: tuple[ConsumerExpectation, ...] = (
    ConsumerExpectation(
        consumer="@journeylab/contracts (generated TypeScript client)",
        operation="POST /trips",
        sends=("CreateTripRequest",),
        reads=("Trip",),
        why="The only operation with both a request and a response body that the "
        "web app will call first; if either shape moves, the client's types move.",
    ),
    ConsumerExpectation(
        consumer="@journeylab/contracts (generated TypeScript client)",
        operation="GET /trips/{tripId}",
        reads=("Trip",),
        why="Every surface that renders a trip reads this shape.",
    ),
    ConsumerExpectation(
        consumer="@journeylab/contracts (generated TypeScript client)",
        operation="POST /trips",
        reads=("Problem",),
        why="Error handling is the branch a consumer is least likely to have "
        "covered by its own tests and most likely to break on; Problem.code is a "
        "closed union generated from ERROR_MODEL.md.",
    ),
    ConsumerExpectation(
        consumer="apps/api (generated Pydantic models)",
        operation="POST /trips",
        sends=("CreateTripRequest",),
        why="The server validates inbound requests against the generated model, so "
        "a request-shape change lands here before it lands anywhere else.",
    ),
)


def operations() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path, item in SPEC["paths"].items():
        for method, operation in item.items():
            if method in ("get", "put", "post", "patch", "delete"):
                out[f"{method.upper()} {path}"] = operation
    return out


class TestConsumerExpectations:
    @pytest.mark.parametrize(
        "expectation", EXPECTATIONS, ids=lambda e: f"{e.consumer.split()[0]} {e.operation}"
    )
    def test_the_operation_still_exists(self, expectation: ConsumerExpectation) -> None:
        assert expectation.operation in operations(), (
            f"{expectation.consumer} calls {expectation.operation}, which no longer exists. "
            f"Why it matters: {expectation.why}"
        )

    @pytest.mark.parametrize(
        "expectation", EXPECTATIONS, ids=lambda e: f"{e.consumer.split()[0]} {e.operation}"
    )
    def test_the_schemas_it_depends_on_still_exist(self, expectation: ConsumerExpectation) -> None:
        declared = set(SPEC["components"]["schemas"])
        for schema in expectation.reads + expectation.sends:
            assert schema in declared, (
                f"{expectation.consumer} depends on schema {schema!r}, which is gone. "
                f"Why it matters: {expectation.why}"
            )

    def test_every_expectation_records_why(self) -> None:
        """Guards the guard. An expectation with no rationale cannot be reviewed for
        removal later, and a suite nobody can prune is a suite everybody skips."""
        for expectation in EXPECTATIONS:
            assert len(expectation.why) > 30, f"{expectation.operation}: rationale too thin"


class TestTheHarnessIsHonestAboutItself:
    def test_there_is_exactly_one_consumer_family_today(self) -> None:
        """This asserts a FACT ABOUT THE WORLD, and it is meant to break.

        When a real external consumer is added in STEP-016, this fails and forces
        whoever adds it to update the surrounding docstring rather than quietly
        inheriting the claim that no external consumer exists. A comment saying
        "update this later" would not have done that.
        """
        internal = {"@journeylab/contracts", "apps/api"}
        consumers = {e.consumer.split()[0] for e in EXPECTATIONS}
        assert consumers <= internal, (
            f"External consumer(s) {sorted(consumers - internal)} now exist. "
            "Update this module's docstring: it currently states that none do, and "
            "CONTRACT_CHANGE_POLICY §3.2 requires unknown consumer coverage to be "
            "stated explicitly rather than assumed to be zero."
        )
