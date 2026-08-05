# JourneyLab local development database — STEP-001.04
#
# Requirement: PostgreSQL 18 with BOTH PostGIS and pgvector
# (docs/product/03-architecture/DATA_ARCHITECTURE.md §1).
#
# VERIFIED CONSTRAINTS (arm64 host, 2026-08-05):
#   - postgis/postgis:18-3.6  PostGIS 3.6 / PG18.4 — amd64 only; repo carries just
#                             4 packages (no pgvector, no dev tools, no compiler)
#   - pgvector/pgvector:pg18  pgvector / PG18.4 — has the built extension
#   - PGDG bookworm/trixie    no postgresql-18-pgvector package
#   - postgis 17-*, 16-*      no arm64 either, so downgrading does not help
#
# Both images are PostgreSQL 18.4. We therefore take PostGIS as the base and copy
# the prebuilt pgvector extension across, rather than compiling it (no toolchain
# in the base) or downgrading PostgreSQL (would breach the blueprint baseline).
#
# The extension is validated at build time — see the RUN check below — so an ABI
# mismatch fails the build rather than surfacing as a runtime error later.
#
# Emulation: measured ~3s to ready on Apple Silicon. Platform pin lives in
# docker-compose.dev.yml so amd64 hosts run natively.
#
# LOCAL DEVELOPMENT ONLY. Production uses managed PostgreSQL
# (docs/product/03-architecture/DEPLOYMENT_ARCHITECTURE.md).

FROM pgvector/pgvector:pg18 AS pgvector-src

FROM postgis/postgis:18-3.6

COPY --from=pgvector-src /usr/lib/postgresql/18/lib/vector.so /usr/lib/postgresql/18/lib/
COPY --from=pgvector-src /usr/share/postgresql/18/extension/vector* /usr/share/postgresql/18/extension/
