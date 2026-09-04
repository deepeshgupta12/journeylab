#!/usr/bin/env bash
# No importable module may shadow the standard library — STEP-007.01.
#
# WHY THIS EXISTS
#   `apps/api/src` and six service roots are on `pythonpath`, so a package named
#   after a stdlib module wins the import. STEP-007.01 created `platform/` and it
#   shadowed `platform.system()` for the whole process — a failure that would have
#   surfaced inside some unrelated dependency, as an AttributeError with nothing
#   pointing back at the package that caused it.
#
#   Caught by importing it deliberately before writing the handler. This makes the
#   next one fail at the gate instead.
#
# Contract: FAILS (exit 1) on any shadowing module. Meta-tested against a seeded one.
set -uo pipefail
cd "$(dirname "$0")/../.."

PY="${PYTHON:-.venv/bin/python}"

scan() {
  "$PY" - <<'PYEOF'
import pathlib, sys, tomllib

config = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
roots = config["tool"]["pytest"]["ini_options"]["pythonpath"]
stdlib = set(sys.stdlib_module_names)
hits = []
for root in roots:
    base = pathlib.Path(root)
    if not base.exists():
        continue
    for entry in base.iterdir():
        if entry.name.startswith((".", "_")):
            continue
        if entry.is_file() and entry.suffix != ".py":
            continue
        name = entry.stem if entry.suffix == ".py" else entry.name
        if name in stdlib:
            hits.append(f"{root}/{entry.name} shadows stdlib '{name}'")
for hit in hits:
    print(hit)
raise SystemExit(1 if hits else 0)
PYEOF
}

echo "=== scanning importable roots for stdlib shadowing ==="
if scan; then
  echo "PASS: no importable module shadows the standard library."
else
  echo ""
  echo "FAIL: a module on pythonpath shadows a standard-library module."
  echo "      Rename it. The failure it causes appears inside an unrelated"
  echo "      dependency, with nothing pointing back here."
  exit 1
fi

# META-TEST: seed a shadowing module and confirm the scan rejects it.
echo ""
echo "=== META-TEST: a seeded shadowing module MUST fail the scan ==="
SEEDED="tools/json.py"
trap 'rm -f "$SEEDED"' EXIT
echo "# seeded by the guard meta-test" > "$SEEDED"
if scan >/dev/null 2>&1; then
  echo "  FAIL: the scan passed with a seeded 'json' shadow — it is not detecting."
  exit 1
fi
echo "  ok   the scan rejects a seeded shadow, so its passes mean something"
rm -f "$SEEDED"
trap - EXIT
exit 0
