-- JourneyLab — 018 a region carries the zone its dates are read in
-- STEP-007.03 · REQ-TRIP-002 · BR-061 §5
--
-- WHY A COLUMN AND NOT A DEFAULT
--   017 gave a region `date_bounds_start` and `date_bounds_end`. Comparing a
--   requested date against those bounds needs an answer to "what is today", and
--   **today is not a property of the server or of the browser.**
--
--   At 23:30 UTC on 4 September it is already the 5th in Zurich and still 13:30 on
--   the 4th in Honolulu. A traveller in Honolulu asking about 5 September in Bern is
--   asking about tomorrow-there, which is today-here. Pick either clock as the
--   default and one of those two people is told their date is in the past when it is
--   not — an off-by-one that renders as a bug in the date picker and is not one.
--
--   So: NOT NULL, no default. 001 defaults `users.time_zone` to 'UTC', which is fine
--   for a display preference and would be a silent wrong answer for a feasibility
--   bound. Declaring a region now forces someone to say where it is.
--
-- WHAT THIS COLUMN IS NOT
--   Not part of the public response. `CoverageRegion` is additionalProperties:false
--   and the traveller never needs the IANA string — the server applies it. Same
--   argument as `accepting_trips` in 017: the contract is not widened to fit an
--   implementation.
--
-- VALIDATION IS SPLIT, DELIBERATELY
--   Postgres checks the column is non-empty. Whether the string is a real IANA zone
--   is checked in Python by `domain.temporal.zone_of`, which raises on an unknown
--   name. `pg_timezone_names` is not a usable CHECK — it is a set-returning function,
--   not immutable, and the list changes with the tzdata package underneath a running
--   database, which would make an existing row fail a constraint it once passed.
--
-- Expand phase over an empty table: additive column, no data to migrate.

BEGIN;

ALTER TABLE coverage_read_model
  ADD COLUMN IF NOT EXISTS time_zone text;

-- The table is empty by construction (016 dropped its only rows and 017 seeded
-- none). If a row somehow exists, it gets UTC and the constraint below still holds
-- — but the region's dates would then be evaluated in a zone nobody chose, so this
-- statement exists to keep the migration total, not because UTC is a good answer.
UPDATE coverage_read_model SET time_zone = 'UTC' WHERE time_zone IS NULL;

ALTER TABLE coverage_read_model ALTER COLUMN time_zone SET NOT NULL;

ALTER TABLE coverage_read_model
  DROP CONSTRAINT IF EXISTS coverage_time_zone_present;
ALTER TABLE coverage_read_model
  ADD CONSTRAINT coverage_time_zone_present CHECK (length(btrim(time_zone)) > 0);

COMMENT ON COLUMN coverage_read_model.time_zone IS
  'IANA zone the region''s date bounds are read in. NOT NULL and no default:
   "is this date in the past" has no answer without it, and the wrong answer is a
   one-day error that looks like a rendering bug. Not exposed publicly.';

COMMIT;
