/**
 * English message catalogue — STEP-003.07.
 *
 * The source language. Translation CONTENT is explicitly out of scope for this
 * sub-step ("Not in this sub-step: RTL implementation; translation content"), so
 * this ships alone and the machinery around it is what is being delivered.
 *
 * Keys are dotted and describe the SURFACE, not the string. `shell.brand` stays
 * correct when the wording changes; `shell.journeylab` does not.
 */

export const en = {
  'shell.brand': 'JourneyLab',
  'shell.skipToContent': 'Skip to main content',
  'nav.label': 'Main navigation',
  'nav.menu': 'Menu',
  'nav.closeMenu': 'Close menu',
  'home.title': 'JourneyLab',
  'home.tagline': 'Compare feasible futures before and during travel',
  'home.sessionEstablished': 'Session established',
  'error.featureUnavailable': '{feature} could not be displayed.',
  'error.tryAgain': 'Try again',
} as const satisfies Readonly<Record<string, string>>;
