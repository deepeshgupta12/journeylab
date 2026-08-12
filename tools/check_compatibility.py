"""The compatibility gate — STEP-004.08 (REQ-PLAT-008).

Diffs `contracts/` against `contracts/baseline/`, classifies every difference with
`tools/contract_diff.py`, and decides whether the build may proceed.

THE RULE, AND THE ONE PLACE IT IS DECIDED
    A BREAKING change requires a major version bump. That is
    `CONTRACT_CHANGE_POLICY` §4, and this file is the only place it is enforced, so
    there is nowhere else for it to drift to.

    POTENTIALLY_BREAKING is reported and does NOT fail the build. §2 says it is
    "treated as breaking unless consumer analysis proves otherwise via the code
    graph" — which is a judgement about consumers, and this repository has one known
    consumer (its own generated client) and no runtime telemetry to find the others.
    Failing on it would make the gate cry wolf on every added enum value, and a gate
    people routinely override with a flag has stopped being a gate. It is printed
    prominently and named in the output as requiring the §2 analysis.

WHY THE BASELINE-PROMOTION CHECK LIVES HERE TOO
    The obvious way around a compatibility gate is to move the baseline. Making the
    snapshot and its recorded digest move together does not prevent that — nothing
    can — but it converts a silent edit into a claimed release. See
    `contracts/baseline/BASELINE.md` §3.

    The digest is recorded IN `BASELINE.md` rather than derived from git history,
    and that choice is deliberate. `git diff HEAD` cannot see a baseline that is not
    yet committed, behaves differently before and after the commit that introduces
    it, and needs history a shallow CI clone does not have. A content digest is the
    same answer everywhere, at any point in the commit cycle, with no network and no
    history — the same argument that chose a committed snapshot over a git tag.
"""

from __future__ import annotations

import hashlib
import pathlib
from typing import Any

import yaml

# `tools/` is the script's own directory and is already on sys.path when this runs
# as a script; it is also on pytest's pythonpath and mypy's mypy_path. No path
# manipulation is needed, and the E402 suppression it used to require is gone with it.
from contract_diff import (
    DiffResult,
    check_deprecation_metadata,
    diff_contracts,
    major_of,
)

REPO = pathlib.Path(__file__).resolve().parents[1]
CURRENT = REPO / "contracts" / "openapi.yaml"
BASELINE_DIR = REPO / "contracts" / "baseline"
BASELINE = BASELINE_DIR / "openapi.yaml"
MARKER = BASELINE_DIR / "BASELINE.md"


def load(path: pathlib.Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    if not isinstance(loaded, dict):
        raise SystemExit(f"{path} is not a mapping")
    return loaded


def _marker_field(label: str) -> str | None:
    """Read one `| Label | value |` row out of BASELINE.md."""
    for line in MARKER.read_text().splitlines():
        if line.startswith(f"| {label} |"):
            return line.split("|")[2].strip().strip("`")
    return None


def recorded_baseline_version() -> str | None:
    """The version BASELINE.md claims the snapshot represents."""
    return _marker_field("Baseline version")


def snapshot_digest() -> str:
    """A digest of the baseline snapshot's contents.

    Every file except BASELINE.md itself — the marker records the digest, so
    including it would make the value depend on itself.

    Paths are relative and sorted so the digest is stable across machines and
    independent of directory-listing order. Content is hashed as bytes rather than
    as parsed YAML: a reformat that changes nothing semantically still changes the
    snapshot, and someone rewriting the baseline should have to say so either way.
    """
    digest = hashlib.sha256()
    files = sorted(
        path for path in BASELINE_DIR.rglob("*") if path.is_file() and path.name != "BASELINE.md"
    )
    for path in files:
        digest.update(str(path.relative_to(BASELINE_DIR)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def report(result: DiffResult) -> None:
    if not result.changes:
        print("  no differences from the baseline")
        return
    for change in sorted(result.changes, key=lambda c: (-c.severity, c.location)):
        print(f"  {change}")


def main() -> int:
    if not BASELINE.exists():
        print(f"FAIL: no baseline at {BASELINE.relative_to(REPO)}")
        print("  Establish one with: pnpm contracts:baseline")
        return 1

    current, baseline = load(CURRENT), load(BASELINE)
    result = diff_contracts(baseline, current)

    current_version = str(current.get("info", {}).get("version", "0.0.0"))
    baseline_version = str(baseline.get("info", {}).get("version", "0.0.0"))

    print(
        f"Comparing contracts/openapi.yaml ({current_version}) "
        f"against baseline ({baseline_version})"
    )
    report(result)

    failures: list[str] = []

    # --- 1. breaking changes need a major bump --------------------------------
    if result.breaking:
        if major_of(current_version) <= major_of(baseline_version):
            failures.append(
                f"{len(result.breaking)} BREAKING change(s) without a major version bump "
                f"({baseline_version} -> {current_version})"
            )
        else:
            print(
                f"\n  {len(result.breaking)} breaking change(s) carried by a major "
                f"version bump ({baseline_version} -> {current_version})."
            )
            print("  CONTRACT_CHANGE_POLICY §3 also requires: migration guide, consumer")
            print("  notice, dual-run window, sunset date, blast-radius record, owner")
            print("  approval and a rollback plan. This gate checks the version only.")

    # --- 2. deprecation metadata ----------------------------------------------
    deprecation_problems = check_deprecation_metadata(current)
    for problem in deprecation_problems:
        print(f"  {problem}")
    if deprecation_problems:
        failures.append(f"{len(deprecation_problems)} deprecated operation(s) missing metadata")

    # --- 3. baseline promotion must be declared -------------------------------
    actual_digest = snapshot_digest()
    recorded_digest = _marker_field("Snapshot digest")
    if recorded_digest is None:
        failures.append("BASELINE.md records no snapshot digest")
    elif recorded_digest != actual_digest:
        print(
            f"\n  baseline snapshot digest {actual_digest}, BASELINE.md records {recorded_digest}"
        )
        failures.append(
            "the baseline snapshot changed but BASELINE.md was not updated. "
            "Promoting a baseline is a release; say so, or restore the snapshot"
        )
    recorded_version = recorded_baseline_version()
    if recorded_version != baseline_version:
        failures.append(
            f"BASELINE.md claims version {recorded_version!r} but the snapshot "
            f"declares {baseline_version!r}"
        )

    if result.potentially_breaking:
        print(
            f"\n  {len(result.potentially_breaking)} POTENTIALLY BREAKING change(s) — "
            f"not failing the build."
        )
        print("  CONTRACT_CHANGE_POLICY §2 treats these as breaking unless consumer")
        print("  analysis proves otherwise. That analysis is a human's, and it has not")
        print("  been done here. Do it before release.")

    if failures:
        print("\nFAIL: contract compatibility (REQ-PLAT-008)")
        for failure in failures:
            print(f"  - {failure}")
        print("\n  A breaking change requires CONTRACT_CHANGE_POLICY §3 in full:")
        print("  new major version, migration guide, consumer notice, dual-run window,")
        print("  sunset date, blast-radius record, owner approval, rollback plan.")
        print("\n  Before release, a breaking change is cheap — see")
        print("  contracts/baseline/BASELINE.md §2. Consider whether you should take it")
        print("  now rather than carry the old shape forever.")
        return 1

    print("\nPASS: no breaking contract change without a major version bump.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
