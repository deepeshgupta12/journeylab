import { CoverageTable } from './coverage-table';
import { fetchCoverage } from './fetch-coverage';

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
          <section aria-labelledby="coverage-status">
            <h2 id="coverage-status">Current data status</h2>
            <p role="status">{HEALTH_SENTENCE[result.coverage.provider_health]}</p>
          </section>

          <CoverageTable regions={result.coverage.regions} />
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

/**
 * One sentence per aggregate value. **No supplier is named**, and there is no
 * count: `REQ-EVID-006` permits disclosing *that* the answer is degraded and
 * forbids disclosing who degraded it, and a count reveals the supply chain's size
 * by another route.
 */
const HEALTH_SENTENCE: Record<string, string> = {
  healthy: 'All data sources are up to date.',
  degraded: 'Some data is older than usual. Affected regions are marked in the table below.',
  unavailable: 'Some data is unavailable. Regions relying on it are not accepting new trips.',
};
