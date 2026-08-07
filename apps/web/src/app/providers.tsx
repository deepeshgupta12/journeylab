'use client';

/**
 * Client provider composition — STEP-003.05.
 *
 * ORDER IS LOAD-BEARING, AND THE SUB-STEP FLAGGED IT
 *   §4 names provider composition order as a low-confidence area affecting
 *   streaming in the App Router. The rationale, outermost to innermost:
 *
 *   1. GlobalErrorBoundary — outermost, so it catches a provider that throws
 *      during its own initialisation. Inside any provider, it could not.
 *   2. Locale — read by everything below it, including error copy. A provider
 *      that renders user-facing text before locale is resolved renders it in the
 *      wrong language and cannot re-render it without remounting.
 *   3. Session — depends on locale for its messages, and everything about data
 *      depends on WHO is asking. STEP-002.02 makes the tenant part of the
 *      request, so nothing that fetches may sit above this.
 *   4. Query/data — innermost of the providers, because a cache keyed without a
 *      session is a cache that can serve one tenant's data to another. This is
 *      the same hazard REQ-SEC-002 names for server caches, arriving on the
 *      client.
 *
 *   The rule that falls out: NOTHING THAT FETCHES SITS ABOVE THE SESSION.
 *
 * Marked `'use client'` because error boundaries require class components and
 * `componentDidCatch`, which do not exist on the server.
 */

import { GlobalErrorBoundary } from '@journeylab/ui';
import type { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <GlobalErrorBoundary
      onError={(error) => {
        // Reporting is wired at STEP-024. Logging the message only — a stack or
        // a provider response may carry data that must not reach telemetry
        // (REQ-PRIV-004). console is the only sink until STEP-024 wires reporting.
        console.error('[journeylab] unhandled error:', error.message);
      }}
    >
      {/* Locale, session and query providers are added by STEP-003.07 and
          STEP-004 respectively. The order above is the contract they must keep. */}
      {children}
    </GlobalErrorBoundary>
  );
}
