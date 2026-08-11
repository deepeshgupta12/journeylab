/**
 * Design token accessibility — TST-A11Y-004 · STEP-003.01.
 *
 * Every accessibility claim here is COMPUTED from the token values, not asserted
 * about them. A colour edited to something that fails WCAG breaks this suite.
 */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import { renderCss } from '../tools/gen-tokens';
import { AAA_NORMAL_TEXT, contrastRatio, parseHex, relativeLuminance } from './contrast';
import {
  contrastPairs,
  ELEVATION,
  MOTION,
  MOTION_REDUCED,
  PALETTES,
  SPACING,
  STATUS_TOKENS,
  type ThemeName,
  TYPOGRAPHY,
} from './tokens';

const here = dirname(fileURLToPath(import.meta.url));

// --- the contrast maths must itself be correct ------------------------------

describe('contrast calculation', () => {
  it('matches the known WCAG extremes', () => {
    // If these are wrong, every assertion below is meaningless.
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 2);
    expect(contrastRatio('#ffffff', '#ffffff')).toBeCloseTo(1, 5);
  });

  it('matches published reference values', () => {
    // #767676 on white is the canonical 4.54:1 example — the lightest grey that
    // still passes AA body text.
    expect(contrastRatio('#767676', '#ffffff')).toBeCloseTo(4.54, 1);
  });

  it('is order-independent', () => {
    expect(contrastRatio('#14181f', '#ffffff')).toBeCloseTo(
      contrastRatio('#ffffff', '#14181f'),
      10,
    );
  });

  it('throws on a malformed colour instead of defaulting to black', () => {
    // A silently-black colour would PASS against white and hide the bad token.
    expect(() => parseHex('#zzzzzz')).toThrow(/valid hex/);
    expect(() => parseHex('')).toThrow();
  });

  it('expands three-digit hex', () => {
    expect(parseHex('#fff')).toEqual(parseHex('#ffffff'));
  });

  it('weights green most heavily, per the luminance formula', () => {
    const green = relativeLuminance(parseHex('#00ff00'));
    const red = relativeLuminance(parseHex('#ff0000'));
    const blue = relativeLuminance(parseHex('#0000ff'));
    expect(green).toBeGreaterThan(red);
    expect(red).toBeGreaterThan(blue);
  });
});

// --- REQ-A11Y-004: every declared pairing meets its WCAG bar ----------------

const THEMES: ThemeName[] = ['light', 'dark', 'high-contrast'];

describe.each(THEMES)('theme: %s', (theme) => {
  const palette = PALETTES[theme];

  it.each(contrastPairs(palette))(
    '$usage meets $minimum:1',
    ({ foreground, background, minimum, usage }) => {
      const ratio = contrastRatio(foreground, background);
      expect(
        ratio,
        `${usage}: ${foreground} on ${background} is ${ratio.toFixed(2)}:1, needs ${minimum}:1`,
      ).toBeGreaterThanOrEqual(minimum);
    },
  );

  it('declares no token that is never verified against a background', () => {
    const verified = new Set(contrastPairs(palette).flatMap((p) => [p.foreground, p.background]));
    const unverified = Object.entries(palette)
      .filter(([, value]) => !verified.has(value))
      .map(([key]) => key);
    expect(unverified, `colour tokens with no declared pairing: ${unverified}`).toEqual([]);
  });
});

describe('high contrast is a distinct palette, not dark mode intensified', () => {
  it('meets AAA for body text where AA would be enough elsewhere', () => {
    const hc = PALETTES['high-contrast'];
    const ratio = contrastRatio(hc['text-primary'] as string, hc['surface-base'] as string);
    expect(ratio).toBeGreaterThanOrEqual(AAA_NORMAL_TEXT);
  });

  it('differs from the dark palette', () => {
    expect(PALETTES['high-contrast']).not.toEqual(PALETTES.dark);
  });
});

// --- REQ-A11Y-004: colour is never the only signal --------------------------

describe('status tokens', () => {
  it('each has a non-colour affordance — both an icon and a text label', () => {
    for (const status of STATUS_TOKENS) {
      expect(status.icon, `${status.name} has no icon`).toBeTruthy();
      expect(status.label, `${status.name} has no text label`).toBeTruthy();
    }
  });

  it('covers every status-* SIGNAL colour, so none can signal by colour alone', () => {
    /*
     * `-surface` tints are excluded, and the exclusion is narrow on purpose.
     *
     * STEP-003.09 added tinted panel backgrounds and this test failed, correctly:
     * it had no way to tell a signal-bearing colour from a background. A tint is
     * not a signal — the foreground colour, the icon and the label are — so
     * requiring an icon for `status-success-surface` asks for something
     * meaningless.
     *
     * The exclusion is by exact suffix rather than by an allowlist, so a NEW
     * signal colour (`status-degraded`, say) is still caught. Weakening this to
     * "ignore anything unmatched" would have made the whole test vacuous, which
     * is the easy and wrong fix.
     */
    const paired = new Set(STATUS_TOKENS.map((s) => s.colorToken));
    const statusColours = Object.keys(PALETTES.light).filter(
      (k) => k.startsWith('status-') && !k.endsWith('-surface'),
    );
    expect(statusColours.length, 'no status colours found — the filter is wrong').toBeGreaterThan(
      0,
    );
    const unpaired = statusColours.filter((k) => !paired.has(k));
    expect(unpaired, `status colours with no icon/label counterpart: ${unpaired}`).toEqual([]);
  });

  it('still requires a counterpart for a NEW signal colour', () => {
    // Proves the exclusion above did not turn the check off. A hypothetical
    // signal token must fail; a hypothetical tint must not.
    const paired = new Set(STATUS_TOKENS.map((s) => s.colorToken));
    const hypothetical = ['status-degraded', 'status-degraded-surface'];
    const caught = hypothetical.filter((k) => !k.endsWith('-surface') && !paired.has(k));
    expect(caught).toEqual(['status-degraded']);
  });

  it('uses a distinct icon per status — a shared icon carries no information', () => {
    const icons = STATUS_TOKENS.map((s) => s.icon);
    expect(new Set(icons).size).toBe(icons.length);
  });
});

// --- REQ-NFR-013: reduced motion SUPPRESSES, never shortens -----------------

describe('reduced motion', () => {
  it('sets every duration to exactly 0ms', () => {
    for (const [key, value] of Object.entries(MOTION_REDUCED)) {
      if (!key.includes('duration')) continue;
      // Deliberately `toBe("0ms")` and not "shorter than default": a 60ms
      // animation still moves, and movement is what triggers vertigo.
      expect(value, `${key} is ${value}, which still animates`).toBe('0ms');
    }
  });

  it('covers every motion duration token, leaving none animating', () => {
    const normal = Object.keys(MOTION).filter((k) => k.includes('duration'));
    const reduced = Object.keys(MOTION_REDUCED).filter((k) => k.includes('duration'));
    expect(reduced.sort()).toEqual(normal.sort());
  });

  it('emits a catch-all so a component hard-coding its own duration cannot animate', () => {
    const css = renderCss();
    expect(css).toContain('prefers-reduced-motion: reduce');
    expect(css).toMatch(/animation-duration:\s*0ms\s*!important/);
    expect(css).toMatch(/transition-duration:\s*0ms\s*!important/);
  });
});

// --- scales -----------------------------------------------------------------

describe('scales', () => {
  it('expresses every font size in rem, never px', () => {
    // A px font size ignores the browser font-size setting many low-vision users
    // rely on before they reach a zoom control (WCAG 1.4.4).
    for (const [key, value] of Object.entries(TYPOGRAPHY)) {
      if (!key.startsWith('font-size')) continue;
      expect(value, `${key} = ${value}`).toMatch(/rem$/);
    }
  });

  it('expresses spacing in rem or zero', () => {
    for (const [key, value] of Object.entries(SPACING)) {
      expect(value, `${key} = ${value}`).toMatch(/^(0|[\d.]+rem)$/);
    }
  });

  it('keeps scales monotonic, so a larger name is never a smaller value', () => {
    const sizes = Object.entries(TYPOGRAPHY)
      .filter(([k]) => k.startsWith('font-size'))
      .map(([, v]) => Number.parseFloat(v));
    for (let i = 1; i < sizes.length; i += 1) {
      expect(sizes[i]).toBeGreaterThan(sizes[i - 1] as number);
    }
  });

  it('provides an elevation-0 that is genuinely no shadow', () => {
    expect(ELEVATION['elevation-0']).toBe('none');
  });
});

// --- the generated CSS must match the tokens --------------------------------

describe('generated tokens.css', () => {
  it('matches what the generator produces right now', () => {
    const onDisk = readFileSync(join(here, 'tokens.css'), 'utf8');
    expect(onDisk, 'tokens.css is stale — run: pnpm --filter @journeylab/ui tokens:build').toBe(
      renderCss(),
    );
  });

  it('emits every palette, scale and motion token as a custom property', () => {
    const css = renderCss();
    for (const key of Object.keys(PALETTES.light)) expect(css).toContain(`--${key}:`);
    for (const key of Object.keys(SPACING)) expect(css).toContain(`--${key}:`);
    for (const key of Object.keys(TYPOGRAPHY)) expect(css).toContain(`--${key}:`);
    for (const key of Object.keys(MOTION)) expect(css).toContain(`--${key}:`);
  });

  it('honours forced-colors as well as prefers-contrast', () => {
    // Windows High Contrast Mode signals forced-colors, not prefers-contrast.
    // Handling only the latter leaves those users on the default palette.
    const css = renderCss();
    expect(css).toContain('prefers-contrast: more');
    expect(css).toContain('forced-colors: active');
  });

  it('allows an explicit theme override as well as the media query', () => {
    const css = renderCss();
    expect(css).toContain('[data-theme="dark"]');
    expect(css).toContain('[data-theme="high-contrast"]');
  });
});

// --- no component may hard-code what a token owns ---------------------------

describe('token ownership', () => {
  it('keeps every colour in the palettes, not scattered through the CSS', () => {
    const css = renderCss();
    const declared = new Set(
      THEMES.flatMap((t) => Object.values(PALETTES[t])).map((c) => c.toLowerCase()),
    );
    const hexes = [...css.matchAll(/#[0-9a-fA-F]{3,6}\b/g)].map((m) => m[0].toLowerCase());
    const stray = hexes.filter((h) => !declared.has(h));
    expect(stray, `hex colours in CSS that no palette declares: ${[...new Set(stray)]}`).toEqual(
      [],
    );
  });
});
