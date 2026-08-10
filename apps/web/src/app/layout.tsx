/**
 * Application frame — STEP-003.05 (REQ-A11Y-001, REQ-NFR-013).
 *
 * LANDMARKS ARE THE KEYBOARD USER'S TABLE OF CONTENTS
 *   A screen reader can jump between banner, navigation, main and contentinfo.
 *   Without them the whole page is one undifferentiated run of text and the only
 *   way through it is Tab, one control at a time.
 *
 * The skip link is FIRST in the document, before the banner. A skip link placed
 * after the navigation skips nothing.
 */

import '@journeylab/ui/tokens.css';
import '@journeylab/ui/components.css';
import './shell.css';

import { documentLocale, SkipLink } from '@journeylab/ui';
import { headers } from 'next/headers';
import type { ReactNode } from 'react';

import { requestI18n } from '@/lib/i18n';

import { AppNavigation } from './navigation';
import { Providers } from './providers';

const MAIN_ID = 'main-content';

export const metadata = {
  title: 'JourneyLab',
  description: 'Compare feasible futures before and during travel',
};

export const viewport = {
  // No maximum-scale and no user-scalable=no: both break pinch zoom, which
  // WCAG 1.4.4 requires up to 200%. They are the most common accessibility
  // regression in a mobile viewport tag.
  width: 'device-width',
  initialScale: 1,
};

/**
 * STEP-003.07 — the locale is negotiated per request rather than hard-coded.
 *
 * COST, STATED PLAINLY
 *   `headers()` opts this layout — and therefore every route beneath it — out of
 *   static rendering. Today that costs nothing: the only page is already
 *   `force-dynamic` because it reads session cookies. It will stop being free the
 *   moment a cacheable marketing or destination page arrives (STEP-007).
 *
 *   The migration when that happens is a locale path segment — `/[locale]/…` —
 *   which lets Next.js pre-render one static variant per locale and drops the
 *   header read entirely. It is not done now because with a single shipped
 *   catalogue it would be routing scaffolding with nothing to route.
 *
 *   `lang` and `dir` come from `documentLocale` together, so they cannot drift
 *   into the mismatched pair (lang="ar" dir="ltr") that is worse than either
 *   alone.
 */
export default async function RootLayout({ children }: { children: ReactNode }) {
  const head = await headers();
  const { locale, t } = requestI18n(head.get('accept-language'));
  const { lang, dir } = documentLocale(locale);

  return (
    <html lang={lang} dir={dir}>
      <body>
        <SkipLink targetId={MAIN_ID}>{t('shell.skipToContent')}</SkipLink>
        <Providers>
          <header className="jl-shell__header">
            <span className="jl-shell__brand">{t('shell.brand')}</span>
            {/*
              Role is hard-coded to `guest` until the session provider lands at
              STEP-004. That is the CONSERVATIVE choice: guest sees the least, so
              a placeholder cannot accidentally reveal an item. It is also
              presentation only — the server refuses regardless of what is drawn.
            */}
            <AppNavigation actorRole="guest" />
          </header>

          {/*
            tabIndex={-1} makes the target programmatically focusable. Browsers
            differ on whether href="#id" moves focus or only scrolls; without this
            the skip link scrolls and leaves focus where it was.
          */}
          <main id={MAIN_ID} tabIndex={-1} className="jl-shell__main">
            {children}
          </main>

          <footer className="jl-shell__footer">
            <span>{t('shell.brand')}</span>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
