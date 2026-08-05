-- JourneyLab local dev bootstrap — STEP-001.04
-- Real migrations live in db/migrations/ from STEP-002 onward; this only makes
-- the required extensions available so a fresh volume matches production shape.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- lexical retrieval (AI-002 hybrid)
CREATE EXTENSION IF NOT EXISTS citext;    -- case-insensitive email (migration 001)
