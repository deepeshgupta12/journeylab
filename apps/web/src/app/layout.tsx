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
import './shell.css';

import { SkipLink } from '@journeylab/ui';
import type { ReactNode } from 'react';

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

export default function RootLayout({ children }: { children: ReactNode }) {
  // Locale becomes dynamic at STEP-003.07; `documentLocale` already derives both
  // attributes together so they cannot drift apart.
  const lang = 'en';
  const dir = 'ltr';

  return (
    <html lang={lang} dir={dir}>
      <body>
        <SkipLink targetId={MAIN_ID} />
        <Providers>
          <header className="jl-shell__header">
            {/* Navigation arrives at STEP-003.06. The landmark exists now so the
                document structure does not change shape when it does. */}
            <span className="jl-shell__brand">JourneyLab</span>
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
            <span>JourneyLab</span>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
