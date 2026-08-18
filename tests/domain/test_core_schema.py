"""Canonical schema, RLS and immutability — TST-SEC-001, TST-SEC-010 · STEP-006.01.

WHAT THESE ARE PROTECTING
    Guarantees that are worthless unless the *database* holds them, because every
    one of them can be bypassed by a code path nobody remembered to check:

      immutability      -> a scenario's inputs edited after the fact, so
                           "reproducible" means "reproduces whatever it says now"
      tenant isolation  -> REQ-SEC-001, and R7 says non-negotiable
      segregation       -> a planning-side injection reaching booking references
      lineage           -> a scenario stored without the four things REQ-CONS-006
                           needs to reproduce it

    Every assertion here runs against real PostgreSQL. A mock cannot tell you
    whether FORCE ROW LEVEL SECURITY is set.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from dbcheck import DSN, requires_db

pytestmark = [pytest.mark.security, requires_db]

ORG = uuid.UUID("66666666-6666-6666-6666-666666666666")
OTHER_ORG = uuid.UUID("77777777-7777-7777-7777-777777777777")
USER = uuid.UUID("6666aaaa-6666-6666-6666-666666666666")

#: Immutable by REQ-CONS-006. Named here so a fourth one added later without a
#: trigger fails `test_every_immutable_table_has_its_trigger`.
IMMUTABLE_TABLES = ("trip_briefs", "evidence_packs", "scenario_versions")


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    with psycopg.connect(DSN, autocommit=True) as connection:
        yield connection


@pytest.fixture
def seeded(conn: psycopg.Connection) -> Iterator[dict[str, uuid.UUID]]:
    """Two tenants, one trip each. Torn down by organization cascade."""
    trip, brief, pack = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with conn.cursor() as cur:
        for org, slug in ((ORG, "step006-a"), (OTHER_ORG, "step006-b")):
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s, %s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                (org, slug, slug),
            )
        cur.execute(
            "INSERT INTO users (id, email) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (USER, "step006@example.test"),
        )
        cur.execute(
            "INSERT INTO trips (id, organization_id, owner_user_id, title, time_zone) "
            "VALUES (%s, %s, %s, 'Bern', 'Europe/Zurich')",
            (trip, ORG, USER),
        )
        cur.execute(
            "INSERT INTO trip_briefs (id, organization_id, trip_id, version, confirmed_by_user_id) "
            "VALUES (%s, %s, %s, 1, %s)",
            (brief, ORG, trip, USER),
        )
        cur.execute(
            "INSERT INTO evidence_packs (id, organization_id, trip_id, coverage_report, fact_count) "
            "VALUES (%s, %s, %s, '{}', 0)",
            (pack, ORG, trip),
        )
    yield {"trip": trip, "brief": brief, "pack": pack}
    with conn.cursor() as cur:
        cur.execute("DELETE FROM organizations WHERE id IN (%s, %s)", (ORG, OTHER_ORG))
        cur.execute("DELETE FROM users WHERE id = %s", (USER,))


# --- immutability ----------------------------------------------------------------


class TestImmutabilityIsEnforcedAtTheDatabase:
    def test_updating_a_trip_brief_is_refused(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID]
    ) -> None:
        """REQ-CONS-006 makes a run reproducible from its inputs. If an input can be
        edited afterwards, "reproducible" means "reproduces whatever it says now",
        which is not a property anyone can rely on."""
        with (
            pytest.raises(psycopg.errors.RestrictViolation, match="append-only"),
            conn.cursor() as cur,
        ):
            cur.execute("UPDATE trip_briefs SET version = 2 WHERE id = %s", (seeded["brief"],))

    def test_updating_an_evidence_pack_is_refused(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID]
    ) -> None:
        """A pack is what a scenario was generated against, so editing one silently
        rewrites the past of every scenario citing it."""
        with pytest.raises(psycopg.errors.RestrictViolation), conn.cursor() as cur:
            cur.execute(
                "UPDATE evidence_packs SET fact_count = 99 WHERE id = %s", (seeded["pack"],)
            )

    def test_immutable_is_not_undeletable(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID]
    ) -> None:
        """The distinction the whole design turns on.

        REQ-PRIV-006 requires deletion to traverse every store. A table that could
        not be deleted from would make the right to erasure unimplementable — a
        privacy defect manufactured by a reproducibility control. UPDATE is blocked;
        DELETE is not.
        """
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trip_briefs WHERE id = %s", (seeded["brief"],))
            assert cur.rowcount == 1

    def test_every_immutable_table_has_its_trigger(self, conn: psycopg.Connection) -> None:
        """A fourth append-only table added without a trigger fails here rather than
        being discovered by an edit that should have been impossible."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.relname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
                "WHERE t.tgname LIKE %s",
                ("%_no_update",),
            )
            assert {row[0] for row in cur.fetchall()} >= set(IMMUTABLE_TABLES)

    def test_the_application_role_holds_no_update_grant_on_them(
        self, conn: psycopg.Connection
    ) -> None:
        """Belt and braces: the grant stops the application, the trigger stops
        everyone including the migration owner. Each covers what the other cannot."""
        with conn.cursor() as cur:
            for table in IMMUTABLE_TABLES:
                cur.execute("SELECT has_table_privilege('journeylab_app', %s, 'UPDATE')", (table,))
                row = cur.fetchone()
                assert row is not None and row[0] is False, table


# --- tenancy -----------------------------------------------------------------------


class TestEveryTenantTableIsIsolated:
    def test_no_tenant_scoped_table_is_missing_forced_rls(self, conn: psycopg.Connection) -> None:
        """TST-SEC-001, derived rather than listed.

        A hardcoded list asserts the current extent of something designed to extend
        — `BUG-021`'s pattern. Deriving the set means the next tenant table is
        covered on the day it is created, by whoever creates it.
        """
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'r'
                  AND n.nspname IN ('public', 'booking')
                  AND NOT c.relforcerowsecurity
                  AND EXISTS (SELECT 1 FROM information_schema.columns col
                              WHERE col.table_schema = n.nspname
                                AND col.table_name = c.relname
                                AND col.column_name = 'organization_id')
            """)
            assert [row[0] for row in cur.fetchall()] == []

    def test_the_domain_tables_actually_arrived(self, conn: psycopg.Connection) -> None:
        """A precondition, not a formality: without it every isolation assertion
        below would pass because the query errors rather than being denied by
        policy. `BUG-007` is what that costs."""
        expected = {
            "traveler_profiles",
            "trips",
            "trip_briefs",
            "places",
            "place_provider_ids",
            "evidence_facts",
            "evidence_packs",
            "evidence_pack_facts",
            "candidates",
            "scenarios",
            "scenario_versions",
            "itinerary_items",
            "impact_events",
            "feedback",
            "consent_records",
        }
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            present = {row[0] for row in cur.fetchall()}
        assert expected <= present, f"missing: {sorted(expected - present)}"

    def test_a_write_without_tenant_context_is_denied(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID]
    ) -> None:
        """`app_current_org()` is NULL when unset, so every policy comparison is NULL
        and no row qualifies. Missing context denies rather than permits."""
        with conn.cursor() as cur, pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("BEGIN; SET LOCAL ROLE journeylab_app")
            cur.execute(
                "INSERT INTO candidates (organization_id, trip_id) VALUES (%s, %s)",
                (ORG, seeded["trip"]),
            )
        conn.rollback()

    def test_one_tenant_cannot_read_another(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID]
    ) -> None:
        with conn.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute("SET LOCAL ROLE journeylab_app")
            # `SET LOCAL` takes no parameters; `set_config(..., true)` is the
            # transaction-scoped equivalent that does, and is what auth.db.bind_tenant
            # uses for exactly this reason.
            cur.execute("SELECT set_config('app.current_org', %s, true)", (str(OTHER_ORG),))
            cur.execute("SELECT count(*) FROM trips WHERE id = %s", (seeded["trip"],))
            row = cur.fetchone()
            assert row is not None and row[0] == 0
            cur.execute("COMMIT")


# --- segregation ---------------------------------------------------------------------


class TestBookingIsSegregatedByGrant:
    def test_the_planning_role_cannot_reach_the_booking_schema(
        self, conn: psycopg.Connection
    ) -> None:
        """TST-SEC-010. Segregation by grant rather than by convention: a
        planning-side injection reaches nothing here, because the role every
        planning query runs as has no USAGE on the schema at all."""
        with conn.cursor() as cur:
            cur.execute("SELECT has_schema_privilege('journeylab_app', 'booking', 'USAGE')")
            row = cur.fetchone()
            assert row is not None and row[0] is False

    def test_the_booking_role_cannot_read_planning_tables(self, conn: psycopg.Connection) -> None:
        """Segregation has to cut both ways or it is a one-directional fence."""
        with conn.cursor() as cur:
            for table in ("trips", "trip_briefs", "evidence_facts"):
                cur.execute(
                    "SELECT has_table_privilege('journeylab_booking', %s, 'SELECT')", (table,)
                )
                row = cur.fetchone()
                assert row is not None and row[0] is False, table

    def test_no_payment_credential_column_exists_anywhere(self, conn: psycopg.Connection) -> None:
        """REQ-BOOK-002 at rest. STEP-005.06 refuses payment-shaped fields at the
        adapter; this is the same rule in the schema — the column a leak would need
        does not exist to be filled in.
        """
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_schema || '.' || table_name || '.' || column_name
                FROM information_schema.columns
                WHERE table_schema IN ('public', 'booking')
                  AND (column_name ~* '(card|pan|cvv|cvc|iban|sort_code|routing|cardholder)'
                       OR column_name ~* 'account_number')
            """)
            assert [row[0] for row in cur.fetchall()] == []


# --- lineage ---------------------------------------------------------------------------


class TestReproducibilityIsAConstraint:
    @pytest.mark.parametrize("omitted", ["brief_id", "pack_id", "solver_config", "seed"])
    def test_a_scenario_cannot_be_stored_without_its_lineage(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID], omitted: str
    ) -> None:
        """REQ-CONS-006 as a NOT NULL rather than a habit. An unreproducible scenario
        cannot be written at all, so the requirement cannot be forgotten by a new
        write path."""
        columns = {
            "organization_id": ORG,
            "trip_id": seeded["trip"],
            "brief_id": seeded["brief"],
            "pack_id": seeded["pack"],
            "solver_config": "{}",
            "seed": 42,
            "model_versions": "{}",
            "objective": "fastest",
        }
        columns[omitted] = None
        names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        with pytest.raises(psycopg.errors.NotNullViolation), conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO scenarios ({names}) VALUES ({placeholders})",  # noqa: S608
                tuple(columns.values()),
            )

    def test_null_island_is_refused_by_the_schema(self, conn: psycopg.Connection) -> None:
        """The same refusal as the adapter, at rest. Every unlocated place would
        otherwise land on one point and a proximity matcher would merge the lot."""
        with (
            pytest.raises(psycopg.errors.CheckViolation, match="null_island"),
            conn.cursor() as cur,
        ):
            cur.execute(
                "INSERT INTO places (name, category, latitude, longitude, time_zone) "
                "VALUES ('x', 'museum', 0, 0, 'Europe/Zurich')"
            )

    def test_money_needs_a_currency_or_it_is_not_a_price(
        self, conn: psycopg.Connection, seeded: dict[str, uuid.UUID]
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation, match="money_complete"),
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                INSERT INTO itinerary_items
                  (organization_id, scenario_version_id, kind, starts_at, ends_at,
                   time_zone, cost_amount_minor)
                VALUES (%s, gen_random_uuid(), 'activity', now(), now(), 'Europe/Zurich', 1234)
            """,
                (ORG,),
            )
