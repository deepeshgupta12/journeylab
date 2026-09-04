-- JourneyLab — 017 coverage regions carry what the contract requires
-- STEP-007.01 · REQ-TRIP-002 · BUG-029
--
-- WHAT THE HANDLER FOUND
--   `CoverageRegion` requires `region_id`, `display_name`, `date_bounds` and
--   `freshness`, and is `additionalProperties: false`. The read model built in
--   STEP-006.09 had `region_id`, `freshness`, `accepting_trips` and `limitations`.
--
--   Two of the four required fields had no source, and one field the model does
--   have is forbidden by the contract. The first attempt at the handler papered
--   over `display_name` by echoing `region_id`, which is the kind of fudge that
--   survives review because the output looks plausible.
--
-- THESE TWO FIELDS ARE DECLARED, NOT DERIVED, AND THAT IS THE POINT
--   `freshness` and `accepting_trips` are folded from `EVT-008` — they are facts
--   about our providers. `display_name` and `date_bounds` are neither: they are the
--   product's statement about what it supports and for which dates. No event
--   produces them and no provider knows them.
--
--   So they are NOT NULL and **no region is seeded**. An empty coverage list is the
--   honest current answer — the product has declared no supported region yet — and
--   the schema now forces whoever declares the first one to supply a display name
--   and a date range rather than inheriting a default nobody chose.
--
--   `accepting_trips` stays in the table and out of the response. STEP-007.03's
--   refusal path needs it; the public contract does not have it, and adding it
--   there would be a contract change made to fit an implementation.
--
-- Expand phase over an empty table: additive columns, no data to migrate.

BEGIN;

ALTER TABLE coverage_read_model
  ADD COLUMN IF NOT EXISTS display_name      text,
  ADD COLUMN IF NOT EXISTS date_bounds_start date,
  ADD COLUMN IF NOT EXISTS date_bounds_end   date;

-- The table is empty by construction (016 dropped its only rows), so NOT NULL is
-- safe to set immediately rather than in a later contract phase.
UPDATE coverage_read_model SET display_name = region_id WHERE display_name IS NULL;
UPDATE coverage_read_model SET date_bounds_start = CURRENT_DATE WHERE date_bounds_start IS NULL;
UPDATE coverage_read_model SET date_bounds_end = CURRENT_DATE WHERE date_bounds_end IS NULL;

ALTER TABLE coverage_read_model ALTER COLUMN display_name      SET NOT NULL;
ALTER TABLE coverage_read_model ALTER COLUMN date_bounds_start SET NOT NULL;
ALTER TABLE coverage_read_model ALTER COLUMN date_bounds_end   SET NOT NULL;

ALTER TABLE coverage_read_model
  DROP CONSTRAINT IF EXISTS coverage_date_bounds_ordered;
ALTER TABLE coverage_read_model
  ADD CONSTRAINT coverage_date_bounds_ordered CHECK (date_bounds_end >= date_bounds_start);

-- A region nobody can name is a region nobody can choose.
ALTER TABLE coverage_read_model
  DROP CONSTRAINT IF EXISTS coverage_display_name_present;
ALTER TABLE coverage_read_model
  ADD CONSTRAINT coverage_display_name_present CHECK (length(btrim(display_name)) > 0);

COMMENT ON COLUMN coverage_read_model.display_name IS
  'Declared, not derived. No event produces it — it is the product naming a region.';
COMMENT ON COLUMN coverage_read_model.date_bounds_start IS
  'Declared coverage window. NOT NULL so declaring a region forces the decision.';
COMMENT ON COLUMN coverage_read_model.accepting_trips IS
  'Derived from freshness. **Deliberately absent from the public response** —
   CoverageRegion is additionalProperties:false and REQ-TRIP-002 enforces refusal
   at trip creation, not in the coverage listing.';

COMMIT;
