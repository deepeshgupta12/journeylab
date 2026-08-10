/**
 * Component gallery — STEP-003.08.
 *
 * The server half: the gate, the page frame and the direction switch. The
 * components themselves are in `gallery-client.tsx`, because a dialog nobody can
 * open is not a dialog under test.
 *
 * `?dir=rtl` renders the whole gallery right-to-left. That is how the RTL
 * criterion carried from STEP-003.07 is finally checked in something that has
 * layout: jsdom has none, so "RTL does not break the layout" had been asserted
 * about a document that was never laid out.
 */

import { notFound } from 'next/navigation';

import './gallery.css';

import { Gallery } from './gallery-client';
import { galleryEnabled } from './gate';

export const dynamic = 'force-dynamic';

export const metadata = {
  title: 'JourneyLab — component gallery',
  // Belt and braces beside the gate: if this ever does reach a public origin,
  // it should not also be indexed.
  robots: { index: false, follow: false },
};

export default async function GalleryPage({
  searchParams,
}: {
  searchParams: Promise<{ dir?: string }>;
}) {
  if (!galleryEnabled()) {
    // notFound(), not a 403. A 403 confirms the route exists.
    notFound();
  }

  const { dir } = await searchParams;
  const rtl = dir === 'rtl';

  return (
    <div dir={rtl ? 'rtl' : 'ltr'} lang={rtl ? 'ar' : 'en'} className="jl-gallery">
      <h1>Component gallery</h1>
      <p>
        Every primitive from STEP-003.01–.07, in every quality state. This route is gated off by
        default and is not part of the product.
      </p>
      <p>
        <a className="jl-gallery__switch" href={rtl ? '/dev/gallery' : '/dev/gallery?dir=rtl'}>
          {rtl ? 'View left-to-right' : 'View right-to-left'}
        </a>
      </p>
      <Gallery />
    </div>
  );
}
