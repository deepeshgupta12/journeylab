import { CoverageTable } from './coverage-table';
import { DegradationNotice } from './degradation';
import { fetchCoverage } from './fetch-coverage';
import { PlanningCheck } from './planning-check';
import { Inspiration, Waitlist } from './waitlist';

/**
 * Public coverage page — STEP-007.02 (REQ-TRIP-002, REQ-A11Y-002, REQ-PRIV-001).
 *
 * REACHABLE WITHOUT AN ACCOUNT, AND WITHOUT A COOKIE
 *   `API-017` is the one unauthenticated operation in the contract, because a
 *   traveller must be able to learn whether their destination is supported before
 *   creating an account. This page is the surface of that decision, so it reads no
 *   session and sets no cookie: asking somebody to be identified in order to be
 *   told "no" is the thing the contract was written to avoid.
 *
 * THE EMPTY STATE IS A REAL ANSWER, NOT A LOADING STATE
 *   No region has been declared yet (`017` seeds none deliberately), so this page
 *   currently renders empty — and it says *why*, because "no regions" and "we could
 *   not ask" are different facts and only one of them is about coverage. The same
 *   distinction the read model draws with `UNAVAILABLE` versus an empty list.
 */

export const dynamic = 'force-dynamic';

export const metadata = {
  title: 'Coverage — JourneyLab',
  description: 'Which regions JourneyLab can plan, for which dates, and what the known limits are.',
};

export default async function CoveragePage() {
  const result = await fetchCoverage();

  return (
    <main id="main">
      <h1>Where JourneyLab can plan</h1>

      <p>
        This page lists every region JourneyLab supports, the dates it can plan for, and the
        limitations we know about. It is here so you can find out before creating an account.
      </p>

      {result.kind === 'unavailable' ? (
        // NOT an empty table. An empty table would say "we support nowhere", which
        // is a claim about coverage; this is a claim about us.
        <section aria-labelledby="coverage-unavailable">
          <h2 id="coverage-unavailable">Coverage could not be loaded</h2>
          <p role="status">
            {result.reason} This is a problem on our side, not a statement that your destination is
            unsupported. Please try again shortly.
          </p>
        </section>
      ) : (
        <>
          {/* STEP-007.05. The sentence, the observation time and the read
              model's own limitations, announced once per state change rather
              than on every render. */}
          <DegradationNotice
            health={result.coverage.provider_health}
            observedAt={result.coverage.observed_at}
            regions={result.coverage.regions}
          />

          <CoverageTable regions={result.coverage.regions} />

          {/* Below the table, deliberately. `REQ-A11Y-002` puts the tabular answer
              first; the form is the interactive path to the same fact and should
              not be the only way to learn it. */}
          <PlanningCheck regions={result.coverage.regions} />

          {/* STEP-007.04, and only on this branch.

              Both of these say "your destination is not supported yet", which is a
              statement about coverage. On the `unavailable` branch we do not know
              whether it is supported — we could not ask — so inviting somebody onto
              a waitlist there would assert the one thing that page exists to avoid
              asserting. */}
          <Waitlist />
          <Inspiration />
        </>
      )}

      <section aria-labelledby="coverage-privacy">
        <h2 id="coverage-privacy">Planning without an account</h2>
        <p>
          You can plan a complete trip as a guest, without giving us an email address. We do not set
          any tracking cookie on this page, and nothing here identifies you.
        </p>
        <p>
          If you later create an account, the trip you were working on comes with you. If you do
          not, it is deleted when your guest session expires.
        </p>
      </section>
    </main>
  );
}
