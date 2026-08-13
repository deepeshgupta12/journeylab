"""Find carried commitments that outlived their target — STEP-001.08 (ENH-002).

WHY THIS EXISTS
    `BUG-022`. `STEP-002.05` wrote "carried to STEP-002.07"; `.07` closed
    `VERIFIED` listing four carried gaps, none of them that one. Nothing failed,
    because a carry is prose and `substep-docs.sh` only checks that a `VERIFIED`
    sub-step has its three records — not that a promise made in one record was
    kept in another.

THE RULE
    A carry naming a target that is ALREADY `VERIFIED` must carry a disposition on
    the same line. Nothing else is checked, and carries to open steps — the normal,
    healthy case — are left entirely alone.

WHAT A DISPOSITION IS, AND WHY IT IS NOT "THE TARGET MENTIONS THE SOURCE"
    A prototype tried that first and it does not survive contact with the
    repository. `STEP-004.01` carried the RFC 9457 migration to `STEP-004.04`, and
    `.04` discharged it by establishing the carry was MISTAKEN — never naming
    `.01`. Discharge has three honest shapes and only one of them looks like doing
    the work:

        done        the work landed in the target
        withdrawn   the carry was wrong
        re-routed   it moved elsewhere

    So the disposition is written where the promise is, by whoever resolves it.

WHAT THIS CANNOT DO
    It proves a carry was CONSIDERED at closure, not that the work was DONE.
    `— withdrawn: nonsense` passes. Same limit as `contracts/baseline/BASELINE.md`
    §3: the check turns silence into a specific, recorded, reviewable claim; it
    cannot make the claim true.
"""

from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"

#: `carried to X`, `carry to X`, `carried into X`. Case-insensitive, backticks
#: optional, and `.07` is the relative form used inside a sub-step's own step.
CARRY = re.compile(
    r"carr(?:ied|y|ies)\s+(?:in)?to\s+`?"
    r"((?:STEP-\d{3}(?:\.\d{2})?)|(?:\.\d{2}))`?",
    re.IGNORECASE,
)

#: The disposition, on the same line as the carry.
#:
#: Deliberately loose about the words after the keyword and strict about the
#: keyword itself. A convention nobody can remember is a convention nobody uses,
#: and the value is in the keyword being greppable.
DISPOSITION = re.compile(r"\b(discharged|withdrawn|superseded)\b", re.IGNORECASE)

#: `STEP-NNN` and `STEP-NNN.MM` are literal placeholders in templates and in the
#: prose that describes this very guard. Treating them as carries would make the
#: guard fire on its own documentation — which it did, on the first run.
PLACEHOLDER = re.compile(r"STEP-N{3}", re.IGNORECASE)

#: Prose that DESCRIBES a carry rather than making one.
#:
#: Needed because this guard's own documentation quotes BUG-022's carry and shows
#: `carried to .07` as an example — so it failed on itself, twice, which is the
#: false-positive tax `ENH-002` predicted. The marker is explicit and greppable
#: rather than the alternative of guessing from quotation marks, which would also
#: exempt real carries written inside table cells.
#:
#: Same spirit as the `rtl-exempt` marker in `tests/guards/logical-css.sh`: an
#: exemption a human wrote and can be asked about, not a heuristic.
EXEMPT = re.compile(r"carry-exempt", re.IGNORECASE)

EXCLUDED_DIRS = ("09-templates",)


@dataclass(frozen=True, slots=True)
class Carry:
    path: pathlib.Path
    line_number: int
    target: str
    text: str


def sub_step_status() -> dict[str, str]:
    """Every sub-step id and its status, read from the records themselves."""
    statuses: dict[str, str] = {}
    for record in (DOCS / "product/08-steps/sub-steps").rglob("*.md"):
        text = record.read_text()
        ident = re.search(r"^sub_step_id:\s*(\S+)", text, re.MULTILINE)
        status = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
        if ident and status:
            statuses[ident.group(1)] = status.group(1)
    return statuses


def _owning_step(path: pathlib.Path) -> str | None:
    """The STEP-NNN a file belongs to, for resolving a relative `.07`."""
    match = re.search(r"STEP-(\d{3})", path.name)
    return f"STEP-{match.group(1)}" if match else None


def find_carries() -> list[Carry]:
    carries: list[Carry] = []
    for path in sorted(DOCS.rglob("*.md")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if PLACEHOLDER.search(line) or EXEMPT.search(line):
                continue
            for match in CARRY.finditer(line):
                target = match.group(1)
                if target.startswith("."):
                    owner = _owning_step(path)
                    if owner is None:
                        # A relative carry outside a step-scoped file cannot be
                        # resolved. Skipped rather than guessed — a wrong target
                        # would produce a confident false report.
                        continue
                    target = owner + target
                carries.append(
                    Carry(path=path, line_number=number, target=target, text=line.strip())
                )
    return carries


def undischarged(carries: list[Carry], statuses: dict[str, str]) -> list[Carry]:
    """Carries whose target has closed and which say nothing about it."""
    return [
        carry
        for carry in carries
        if statuses.get(carry.target) == "VERIFIED" and not DISPOSITION.search(carry.text)
    ]


def main() -> int:
    statuses = sub_step_status()
    carries = find_carries()
    open_ones = undischarged(carries, statuses)

    print(
        f"Scanned {len(list(DOCS.rglob('*.md')))} documents; found {len(carries)} carried commitment(s)."
    )

    if not open_ones:
        closed = sum(1 for c in carries if statuses.get(c.target) == "VERIFIED")
        print(
            f"  {closed} point at a closed sub-step and all carry a disposition; "
            f"{len(carries) - closed} point at work still open."
        )
        print("\nPASS: no carried commitment outlived its target unrecorded.")
        return 0

    print("\nFAIL: a commitment was carried to a sub-step that has since closed,")
    print("      and nothing on that line says what became of it.\n")
    for carry in open_ones:
        relative = carry.path.relative_to(REPO)
        print(f"  {relative}:{carry.line_number}")
        print(f"    carried to {carry.target}, which is VERIFIED")
        print(f"    {carry.text[:120]}")
        print()

    print("  This is BUG-022's shape: STEP-002.05 carried session revocation to")
    print("  STEP-002.07, .07 closed without it, and nothing failed for six sub-steps.")
    print()
    print("  Add a disposition to the line — whichever is true:")
    print("    — discharged at STEP-NNN.MM     the work was done, here")
    print("    — withdrawn: <reason>           the carry was mistaken")
    print("    — superseded by <what>          it moved, and this says where")
    print()
    print("  Re-routing is allowed and deliberately visible: writing it down is the")
    print("  point, so a promise that keeps moving can be counted.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
