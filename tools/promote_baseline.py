"""Promote the current contracts to the compatibility baseline — STEP-004.08.

`pnpm contracts:baseline`

PROMOTING A BASELINE IS DECLARING A RELEASE
    After this runs, every breaking change made before now becomes invisible to
    `tests/guards/contract-compatibility.sh` — that is what a baseline is for, and
    it is why this is not something to run to make a red build go green.

    The script deliberately does NOT update `BASELINE.md`. It prints the new digest
    and requires a human to write it in alongside the version, the commit and the
    date. Automating that would mean the one artefact recording "somebody decided to
    release this" could be produced by a script nobody read.
"""

from __future__ import annotations

import shutil

# `tools/` is the script's own directory and is already on sys.path when this runs
# as a script; it is also on pytest's pythonpath and mypy's mypy_path. No path
# manipulation is needed, and the E402 suppression it used to require is gone with it.
from check_compatibility import (
    BASELINE_DIR,
    REPO,
    snapshot_digest,
)

SOURCES = ("openapi.yaml", "asyncapi.yaml")
SOURCE_DIRS = ("jsonschema", "schemas")


def main() -> int:
    contracts = REPO / "contracts"

    for name in SOURCES:
        shutil.copy2(contracts / name, BASELINE_DIR / name)
    for name in SOURCE_DIRS:
        target = BASELINE_DIR / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(contracts / name, target)

    digest = snapshot_digest()
    print(f"baseline updated from contracts/ — new digest {digest}")
    print()
    print("NOW EDIT contracts/baseline/BASELINE.md, in this same commit:")
    print(f"  | Snapshot digest | `{digest}` |")
    print("  | Baseline version | the version being released |")
    print("  | Baseline commit  | the commit being released |")
    print()
    print("The guard fails until the digest matches, which is the point: promoting a")
    print("baseline is a release, and a release is a decision somebody records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
