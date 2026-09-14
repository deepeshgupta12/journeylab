'use client';

import { useEffect, useState } from 'react';
import type { Coverage, CoverageRegion } from './fetch-coverage';

/**
 * The degraded-state banner — STEP-007.05 (REQ-EVID-006, REQ-EVID-001, REQ-A11Y-001).
 *
 * WHAT REQ-EVID-006 ACTUALLY FORBIDS
 *   Not caching. *"Degradation masked by cached data presented as current."* The
 *   API caches coverage for 30 seconds and stamps `observed_at` **before** storing
 *   it, so a cache hit carries the timestamp of the read that filled the cache.
 *   This component's job is to put that on the screen — a response that says how
 *   old it is has stopped presenting itself as current, which is the whole
 *   requirement.
 *
 *   A page that rendered coverage and dropped `observed_at` would be presenting an
 *   estimate as confirmed (`REQ-EVID-003`), and the server could do nothing about
 *   it. So the time is rendered unconditionally, healthy or not.
 *
 * THE TEXT COMES FROM THE READ MODEL, NOT FROM HERE
 *   `limitations` is produced by the projection and carried through the contract.
 *   This component selects and arranges it; it does not write it. A sentence
 *   composed here would be a second description of a provider's state, in a second
 *   language, drifting from the first — `BUG-029` exactly.
 *
 *   The one thing that IS written here is the sentence per aggregate value, and
 *   that is a label for an enum rather than a claim about the world.
 *
 * ANNOUNCED ONCE PER STATE CHANGE, NOT PER RENDER
 *   A live region that re-announces on every render interrupts a screen-reader
 *   user reading the table below it, repeatedly, to tell them something they were
 *   already told. The effect is keyed on the health value, and a re-render with an
 *   unchanged value does not re-announce.
 *
 *   `data-announce-count` exists so that property can be tested. "Announced once"
 *   is otherwise invisible — the DOM looks identical whether the text was set once
 *   or fifty times — and an unobservable property is one nothing is checking. Same
 *   reasoning as `aria-rowcount` on the data table.
 */

/**
 * One sentence per aggregate value. **No supplier is named**, and there is no
 * count: `REQ-EVID-006` permits disclosing *that* the answer is degraded and
 * forbids disclosing who degraded it. A count reveals the supply chain's size by
 * another route.
 */
const HEALTH_SENTENCE: Record<Coverage['provider_health'], string> = {
  healthy: 'All data sources are up to date.',
  degraded: 'Some data is older than usual. Affected regions are marked in the table below.',
  unavailable: 'Some data is unavailable. Regions relying on it are not accepting new trips.',
};

/** Renders a timestamp as something a person reads, falling back to the raw value. */
function readableTime(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed
    .toISOString()
    .replace('T', ' ')
    .replace(/\.\d+Z$/, ' UTC');
}

export function DegradationNotice({
  health,
  observedAt,
  regions,
}: {
  readonly health: Coverage['provider_health'];
  readonly observedAt: string;
  readonly regions: readonly CoverageRegion[];
}) {
  const [announcement, setAnnouncement] = useState('');
  const [announceCount, setAnnounceCount] = useState(0);

  useEffect(() => {
    // THE DEPENDENCY ARRAY IS THE MECHANISM. There is deliberately no second guard.
    //
    // The first version also kept the last announced value in a `useRef` and
    // returned early when it matched — defence in depth against somebody adding an
    // unrelated dependency later. Mutation testing killed the idea rather than the
    // mutant: removing that guard changed no observable behaviour, because `[health]`
    // already prevents the effect from re-running, so no test could tell the two
    // versions apart.
    //
    // A guard nothing can distinguish from its absence is not protection, it is
    // code that will be maintained forever on the strength of a comment. The
    // protection that IS real is this array, and "DOES NOT re-announce when
    // re-rendered with the same state" in `degradation.test.tsx` fails the moment it
    // is widened — mutant M9b, `BR-064` §7.
    setAnnouncement(HEALTH_SENTENCE[health]);
    setAnnounceCount((n) => n + 1);
  }, [health]);

  // Straight from the read model. Deduplicated because two regions degraded by the
  // same upstream carry the same sentence, and saying it twice reads as two faults.
  const limitations = Array.from(
    new Set(regions.flatMap((region) => region.limitations ?? [])),
  ).sort();

  return (
    <section aria-labelledby="coverage-status">
      <h2 id="coverage-status">Current data status</h2>

      {/*
       * `aria-live="polite"`, not `role="alert"`. Degradation is a disclosure, not
       * an emergency — the traveller can still read the page and most of it is
       * still true. An assertive region here would interrupt them mid-sentence to
       * say "some data is older than usual", which is the wrong urgency and the
       * fastest way to teach somebody to ignore the region entirely.
       */}
      <p aria-live="polite" data-health-announcement data-announce-count={announceCount}>
        {announcement || HEALTH_SENTENCE[health]}
      </p>

      {/*
       * RENDERED WHETHER OR NOT ANYTHING IS DEGRADED.
       *
       * Showing the observation time only when degraded would make its presence a
       * degradation signal in itself, and — worse — would leave the healthy answer
       * with nothing to say how old it is, which is the case where a stale cached
       * "all good" does the most damage.
       */}
      <p data-observed-at={observedAt}>
        Read at <time dateTime={observedAt}>{readableTime(observedAt)}</time>. Coverage is cached
        briefly, so this is the moment the answer was taken, not the moment you asked for it.
      </p>

      {limitations.length > 0 ? (
        <>
          <h3>Known limitations right now</h3>
          {/* Verbatim from the read model. Summarising a limitation to fit a
              layout is a limitation the traveller did not read. */}
          <ul>
            {limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}
