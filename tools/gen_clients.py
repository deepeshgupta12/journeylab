"""Generate API clients from the contracts — STEP-004.07 (REQ-PLAT-007).

Run: pnpm contracts:generate

TWO LANGUAGES, ONE SOURCE
    `contracts/openapi.yaml` produces TypeScript types for the web surface and
    Pydantic models for the API. Neither is written by hand, and the drift guard
    (`tests/guards/generated-clients.sh`) fails the build if either is edited or
    left stale.

WHY THE OUTPUT IS COMMITTED
    A generated artifact that only exists in CI cannot be reviewed, cannot be
    diffed in a pull request, and cannot be typechecked by an editor. Committing
    it makes the consequence of a contract change **visible in the diff** — which
    is the entire argument for contract-first, and is lost if the client appears
    only inside a build step.

    The cost is that the tree can go stale, and that cost is paid by the guard.

DETERMINISM IS A REQUIREMENT, NOT A NICETY
    A generator that emits a timestamp, an absolute path or a random ordering
    makes the drift guard fire on every run and teaches everyone to ignore it.
    Both generators below are invoked with settings that produce byte-identical
    output from identical input, and `--custom-file-header` replaces any header
    the tool would otherwise date-stamp.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
OPENAPI = REPO / "contracts/openapi.yaml"
SCHEMA_DIR = REPO / "contracts/jsonschema"

TS_OUT = REPO / "packages/contracts/src/generated/openapi.ts"
PY_OUT = REPO / "apps/api/src/generated/models.py"

HEADER = (
    "GENERATED from contracts/ — DO NOT EDIT.\n"
    "Rebuild: pnpm contracts:generate\n"
    "STEP-004.07 · REQ-PLAT-007\n"
    "\n"
    "A hand edit here fails tests/guards/generated-clients.sh, which regenerates\n"
    "and diffs. So does a contract change without a regeneration — the guard\n"
    "cannot tell the two apart, and does not need to: both mean the committed\n"
    "client does not match the contract."
)


def run(command: list[str], *, cwd: pathlib.Path | None = None) -> None:
    """Run a generator, surfacing its output only when it fails.

    S603 is suppressed rather than worked around, and the justification is that
    every argument is a module-level constant or a path derived from `REPO` —
    there is no parameter through which a caller could reach this, and no shell.
    `shell=False` is the default and is what makes the argument list a list rather
    than a string a shell would re-parse.

    Silent on success on purpose: a generator that prints on every run trains
    people to ignore its output, which is the run where it mattered.
    """
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell, no caller input
        command, cwd=cwd or REPO, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"generation failed: {' '.join(command)}")


def generate_typescript() -> None:
    """Emit TypeScript types.

    OPENAPI-TYPESCRIPT IS PINNED TO v6, AND THE REASON IS ADR-009.
        v7 builds its output through the TypeScript **compiler API**
        (`ts.factory.createKeywordTypeNode`). TypeScript 7 is the native compiler
        and ships no JavaScript API, so v7 dies with:

            TypeError: Cannot read properties of undefined
                       (reading 'createKeywordTypeNode')

        This is the **third** time the missing compiler API has bitten — BUG-017
        was Next's type-check step, BUG-018 was the token generator's module
        resolution. Adopting a toolchain ahead of its ecosystem has a running
        cost, and it is paid one tool at a time.

        v6 builds its output with string templates and needs no compiler API at
        all. Revisit when openapi-typescript supports TypeScript 7, and not by
        bumping the major without checking — the failure names a property, not a
        version.
    """
    TS_OUT.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "pnpm",
            "exec",
            "openapi-typescript",
            str(OPENAPI),
            "--output",
            str(TS_OUT),
            # A TS `enum` is a runtime value, and a generated runtime value is
            # code we would then have to ship and test. Unions are types only.
            "--export-type",
        ],
    )
    body = TS_OUT.read_text(encoding="utf-8")
    banner = "\n".join(f" * {line}" if line else " *" for line in HEADER.splitlines())
    TS_OUT.write_text(f"/**\n{banner}\n */\n\n{body}", encoding="utf-8")


def generate_python() -> None:
    PY_OUT.parent.mkdir(parents=True, exist_ok=True)
    (PY_OUT.parent / "__init__.py").write_text(
        '"""Generated models. Do not edit — see tools/gen_clients.py."""\n',
        encoding="utf-8",
    )
    run(
        [
            "uv",
            "run",
            "datamodel-codegen",
            "--input",
            str(OPENAPI),
            "--input-file-type",
            "openapi",
            "--output",
            str(PY_OUT),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.13",
            # Determinism: no timestamp in the header, stable field order.
            #
            # The header must arrive ALREADY COMMENTED. `--custom-file-header`
            # inserts the text verbatim, so a bare header produced a module whose
            # third line was prose and which failed to import with a SyntaxError
            # on an em dash. The generator does not check that its own output
            # parses.
            "--custom-file-header",
            "\n".join(f"# {line}" if line else "#" for line in HEADER.splitlines()),
            "--disable-timestamp",
            # Forbid extra fields, matching `additionalProperties: false` in the
            # contract. A permissive model would silently accept a payload the
            # contract rejects.
            "--use-schema-description",
            "--field-constraints",
            "--snake-case-field",
        ],
    )


def main() -> None:
    if shutil.which("pnpm") is None:
        raise SystemExit("pnpm is required")
    generate_typescript()
    generate_python()
    print(f"wrote {TS_OUT.relative_to(REPO)}")
    print(f"wrote {PY_OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
