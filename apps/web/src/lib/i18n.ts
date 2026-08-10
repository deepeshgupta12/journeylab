/**
 * Request-scoped internationalisation — STEP-003.07 (REQ-NFR-007, REQ-NFR-008).
 *
 * This is the file the sub-step names. It does one job: turn an incoming request
 * into an explicit `{ locale, timeZone, catalogue }` triple that is then passed
 * down as a value. The formatters in `@journeylab/ui` take those as required
 * arguments and read nothing ambient — see `packages/ui/src/i18n/datetime.ts`.
 *
 * ACCEPT-LANGUAGE IS UNTRUSTED INPUT
 *   `REQ-SEC-006` — retrieved content is data, never instruction. A header is the
 *   same. The naive implementation of locale loading is:
 *
 *       await import(`./messages/${locale}.json`)   // NEVER
 *
 *   With `Accept-Language: ../../../../etc/passwd` that is a path traversal, and
 *   with a bundler that inlines the directory it is an arbitrary-module read. So
 *   the header is only ever used to SELECT from a fixed, statically-imported map.
 *   A locale that is not a key resolves to the fallback; nothing is constructed
 *   from the string.
 *
 *   The header is also length-capped before parsing. A 2 MB Accept-Language with
 *   fifty thousand q-weighted tags is a cheap way to spend server CPU on every
 *   request.
 *
 * THE TIME ZONE IS THE TRIP'S, NOT THE READER'S
 *   Deliberate, and worth stating because it looks like a bug. A traveller
 *   checking their Tokyo itinerary from London wants Tokyo times: "the ferry
 *   leaves at 07:40" is useful, "the ferry leaves at 23:40 yesterday" is true and
 *   useless. Until a trip exists (STEP-009) the default below applies.
 */

import {
  createTranslator,
  FALLBACK_LOCALE,
  type MessageCatalogue,
  resolveLocale,
  type Translator,
} from '@journeylab/ui';

import { en } from './messages/en';

/**
 * Every catalogue the application ships, statically imported.
 *
 * Static because it is what makes the traversal above impossible, and because a
 * dynamic import inside a server component turns a static page into a streamed
 * one — see the note in `packages/ui/src/i18n/messages.ts`.
 */
export const CATALOGUES: Readonly<Record<string, MessageCatalogue>> = { en };

export const AVAILABLE_LOCALES = Object.keys(CATALOGUES);

/**
 * The invariant that lets `requestI18n` index `CATALOGUES` without a fallback
 * chain: `negotiateLocale` only ever returns a key of `CATALOGUES` or
 * `FALLBACK_LOCALE`, so the fallback must itself be a key.
 *
 * Checked at module load. A build that renamed or dropped the English catalogue
 * fails on the first import — loudly, in CI — rather than serving a page of raw
 * message keys to a user.
 */
if (!Object.hasOwn(CATALOGUES, FALLBACK_LOCALE)) {
  throw new Error(
    `the fallback locale "${FALLBACK_LOCALE}" has no catalogue; ` +
      `shipped: ${AVAILABLE_LOCALES.join(', ') || '(none)'}`,
  );
}

const FALLBACK_CATALOGUE = CATALOGUES[FALLBACK_LOCALE] as MessageCatalogue;

/**
 * Time zone used before a trip supplies one.
 *
 * UTC, not the server's zone. A server zone is an accident of deployment: the
 * same code would render different times in eu-west-1 and us-east-1, and the
 * difference would only show up in production.
 */
export const DEFAULT_TIME_ZONE = 'UTC';

/** Longest Accept-Language we will parse. Beyond this the header is ignored. */
const MAX_ACCEPT_LANGUAGE = 512;

/** A well-formed BCP 47 tag, conservatively. Anything else is discarded unread. */
const LANGUAGE_TAG = /^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$/;

interface WeightedTag {
  readonly tag: string;
  readonly quality: number;
}

/**
 * Parse `Accept-Language` into tags ordered by preference.
 *
 * Malformed entries are dropped rather than rejecting the whole header: a client
 * sending one bad tag among five good ones should still get a sensible language,
 * and there is no security value in being strict once nothing is constructed from
 * the string.
 */
export function parseAcceptLanguage(header: string | null | undefined): WeightedTag[] {
  if (!header) return [];
  if (header.length > MAX_ACCEPT_LANGUAGE) return [];

  const parsed: WeightedTag[] = [];
  for (const part of header.split(',')) {
    const [rawTag, ...params] = part.split(';');
    const tag = (rawTag ?? '').trim();
    if (tag === '' || tag === '*' || !LANGUAGE_TAG.test(tag)) continue;

    const qParam = params.map((p) => p.trim()).find((p) => p.startsWith('q='));
    const quality = qParam ? Number(qParam.slice(2)) : 1;
    // NaN and out-of-range weights are treated as "no preference expressed"
    // rather than as zero, which would silently discard the tag.
    const q = Number.isFinite(quality) && quality >= 0 && quality <= 1 ? quality : 1;
    if (q === 0) continue; // q=0 means "explicitly not this one".
    parsed.push({ tag, quality: q });
  }
  // Stable sort by descending quality; equal weights keep header order, which is
  // what RFC 9110 says preference means.
  return parsed
    .map((entry, index) => ({ entry, index }))
    .sort((a, b) => b.entry.quality - a.entry.quality || a.index - b.index)
    .map(({ entry }) => entry);
}

/** Negotiate a shipped locale from the header. Never throws; always returns one. */
export function negotiateLocale(
  header: string | null | undefined,
  available: readonly string[] = AVAILABLE_LOCALES,
): string {
  for (const { tag } of parseAcceptLanguage(header)) {
    const resolved = resolveLocale(tag, available, '');
    if (resolved !== '') return resolved;
  }
  return FALLBACK_LOCALE;
}

export interface RequestI18n {
  readonly locale: string;
  readonly timeZone: string;
  readonly t: Translator['t'];
  readonly translator: Translator;
}

/**
 * Build the request's i18n context.
 *
 * Called once per request by a server component and passed down. Nothing here is
 * memoised in module scope: a cached "current locale" on a server that handles
 * many requests concurrently is shared mutable state, and the failure mode is one
 * user seeing another user's language.
 */
export function requestI18n(
  header: string | null | undefined,
  timeZone: string = DEFAULT_TIME_ZONE,
): RequestI18n {
  const locale = negotiateLocale(header);
  // `?? {}` was the first version of this line, and it was worse than nothing: a
  // missing catalogue would have produced a page of raw message keys with no
  // error anywhere, and a mutation test proved the branch could never be reached
  // to be exercised either. The invariant below is checked once at module load,
  // where a build that dropped a catalogue fails loudly instead.
  const catalogue = CATALOGUES[locale] as MessageCatalogue;
  const translator = createTranslator(locale, catalogue, FALLBACK_CATALOGUE);
  return { locale, timeZone, t: translator.t, translator };
}
