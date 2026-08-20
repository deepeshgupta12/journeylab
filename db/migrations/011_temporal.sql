-- JourneyLab — 011 temporal integrity
-- STEP-006.02 · REQ-DATA-007, REQ-EVID-002 · BR-051
--
-- THE CONSTRAINT THIS MIGRATION ALMOST ADDED, AND WHY IT WOULD HAVE BEEN A DEFECT
--
--   The obvious rule for a fact table is "two facts about the same field of the
--   same place must not have overlapping effective windows" — otherwise the
--   solver picks one arbitrarily and the answer depends on row order.
--
--   That rule is wrong here, and not marginally. REQ-EVID-002 requires
--   conflicting evidence to stay visible and never be averaged or resolved away.
--   Two sources disagreeing about the same opening hours over the same dates IS
--   the conflicting evidence the product promises to keep. An exclusion
--   constraint over (place, field) would make storing it impossible — the schema
--   would enforce a requirement violation, and the second source's fact would be
--   rejected at insert with a constraint error that looks like a data bug.
--
--   The defensible line is narrower: **one source must not contradict itself.**
--   Two facts from the same source, about the same field of the same place, with
--   overlapping effective windows, are not evidence of disagreement — they are
--   evidence that we ingested the same thing twice or mis-parsed a window. So the
--   exclusion key includes source_id, and cross-source conflict remains storable,
--   visible and the solver's problem to surface rather than the schema's to
--   prevent.
--
-- Expand phase: additive. Safe to revert.

BEGIN;

-- Needed to mix equality columns with a range in one exclusion constraint.
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- The effective window as a range, generated rather than stored separately so it
-- cannot drift from the columns it is derived from. `effective_to` NULL is
-- open-ended, which upper-bound-infinity expresses exactly.
ALTER TABLE evidence_facts
  ADD COLUMN IF NOT EXISTS effective_range tstzrange
  GENERATED ALWAYS AS (tstzrange(effective_from, effective_to, '[)')) STORED;

-- ONE SOURCE MUST NOT CONTRADICT ITSELF.
-- Deliberately keyed by source_id: see the header. Cross-source disagreement is
-- REQ-EVID-002 evidence and stays storable.
ALTER TABLE evidence_facts
  DROP CONSTRAINT IF EXISTS evidence_facts_no_self_overlap;
ALTER TABLE evidence_facts
  ADD CONSTRAINT evidence_facts_no_self_overlap
  EXCLUDE USING gist (
    organization_id WITH =,
    -- COALESCED, and this is not cosmetic. In an exclusion constraint a NULL
    -- column never conflicts, because NULL = NULL is unknown — so two rows with
    -- no place_id would escape the check entirely and the constraint would
    -- silently not apply to region-level facts. Found by the test for it.
    (coalesce(place_id, '00000000-0000-0000-0000-000000000000'::uuid)) WITH =,
    field_class     WITH =,
    source_id       WITH =,
    effective_range WITH &&
  );

COMMENT ON CONSTRAINT evidence_facts_no_self_overlap ON evidence_facts IS
  'STEP-006.02. One source may not state two overlapping values for one field.
   Keyed by source_id ON PURPOSE — two SOURCES disagreeing is REQ-EVID-002
   evidence and must remain storable.';

-- A local date without a zone is wrong by an hour twice a year and wrong by a day
-- at the boundaries. Enforced rather than documented.
ALTER TABLE trips
  DROP CONSTRAINT IF EXISTS trips_time_zone_present;
ALTER TABLE trips
  ADD CONSTRAINT trips_time_zone_present CHECK (length(btrim(time_zone)) > 0);

ALTER TABLE itinerary_items
  DROP CONSTRAINT IF EXISTS itinerary_items_time_zone_present;
ALTER TABLE itinerary_items
  ADD CONSTRAINT itinerary_items_time_zone_present CHECK (length(btrim(time_zone)) > 0);

COMMIT;
