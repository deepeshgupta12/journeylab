"""Seed and remove the browser suite's reserved region — BUG-038.

`uv run python tools/e2e_region.py seed`
`uv run python tools/e2e_region.py remove`

WHY THE BROWSER SUITE OWNS ITS OWN DATA
    Until BUG-038 the Playwright suite assumed `coverage_read_model` was empty — not
    as a fixture it created, but as a fact about whatever database it happened to be
    pointed at. That held only because no region had ever been declared. The moment
    one was (for the owner's first manual review), two browser tests would have gone
    red, and the one test the fix needed — a browser actually submitting the date
    form — had nothing to submit against.

    So the suite seeds one reserved region before it runs and removes it, with any
    waitlist rows its run created, afterwards. Called from
    `apps/web/src/test/global-setup.ts` and `global-teardown.ts`.

THE DSN IS REQUIRED, NOT DEFAULTED
    The one default for the browser suite's database lives in
    `apps/web/src/test/dsn.ts`, where `playwright.config.ts` also reads it for the
    API it starts. A second default here would be the two-names bug `tests/dbcheck.py`
    records (STEP-001.07), one layer over.

WHAT IS RESERVED
    The region id `e2e-bern` and any waitlist row whose `region_query` starts with
    `e2e-run-`. Nothing else is touched. The planning window is computed relative to
    today so the tests that use it do not rot: one year back, three years forward.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta

import psycopg

REGION_ID = "e2e-bern"
REGION_NAME = "E2E Bern (browser suite)"
WAITLIST_MARKER = "e2e-run-"


def dsn() -> str:
    value = os.environ.get("JOURNEYLAB_DATABASE_URL", "").strip()
    if not value:
        sys.exit(
            "JOURNEYLAB_DATABASE_URL is required. This tool has no default on purpose; "
            "the browser suite's one default is apps/web/src/test/dsn.ts."
        )
    return value


def seed(cur: psycopg.Cursor) -> dict[str, object]:
    """Insert the region, or reset it to the known state if a crashed run left it."""
    today = datetime.now(UTC).date()
    start = today - timedelta(days=365)
    end = today + timedelta(days=3 * 365)
    limitations = json.dumps(["Seeded by the browser test suite; removed on teardown"])
    cur.execute(
        "INSERT INTO coverage_read_model (region_id, display_name, date_bounds_start, "
        "date_bounds_end, time_zone, freshness, accepting_trips, limitations) "
        "VALUES (%s, %s, %s, %s, 'Europe/Zurich', 'current', true, %s::jsonb) "
        "ON CONFLICT (region_id) DO UPDATE SET display_name = EXCLUDED.display_name, "
        "date_bounds_start = EXCLUDED.date_bounds_start, "
        "date_bounds_end = EXCLUDED.date_bounds_end, time_zone = EXCLUDED.time_zone, "
        "freshness = 'current', accepting_trips = true, limitations = EXCLUDED.limitations",
        (REGION_ID, REGION_NAME, start, end, limitations),
    )
    # A previous run that did not reach teardown leaves its waitlist rows behind.
    # They are removed here and COUNTED, so a missing teardown is visible in the
    # setup output rather than silently absorbed.
    cur.execute(
        "DELETE FROM waitlist_entries WHERE region_query LIKE %s",
        (f"{WAITLIST_MARKER}%",),
    )
    return {
        "region_id": REGION_ID,
        "window": [start.isoformat(), end.isoformat()],
        "leftover_waitlist_rows_removed": cur.rowcount,
    }


def remove(cur: psycopg.Cursor) -> dict[str, object]:
    cur.execute(
        "DELETE FROM waitlist_entries WHERE region_query LIKE %s",
        (f"{WAITLIST_MARKER}%",),
    )
    waitlist_rows = cur.rowcount
    cur.execute("DELETE FROM coverage_read_model WHERE region_id = %s", (REGION_ID,))
    return {
        "region_id": REGION_ID,
        "region_rows_removed": cur.rowcount,
        "waitlist_rows_removed": waitlist_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("seed", "remove"))
    args = parser.parse_args(argv)

    with psycopg.connect(dsn()) as conn, conn.cursor() as cur:
        summary = seed(cur) if args.action == "seed" else remove(cur)
        conn.commit()
    print(json.dumps({"action": args.action, **summary}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
