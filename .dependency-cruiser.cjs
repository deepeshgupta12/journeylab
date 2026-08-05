/**
 * JourneyLab module boundary enforcement — STEP-001.02
 *
 * Enforces ADR-003 (modular monolith plus isolated workers). Without this,
 * the monolith degrades into a structure that cannot be split later, and the
 * "split only when scaling justifies it" decision becomes unavailable.
 *
 * Core rule: a module's internals are private. Cross-module imports must go
 * through the package's public entry point, never reach into `src/` internals.
 */
module.exports = {
  forbidden: [
    {
      name: 'no-cross-module-internals',
      severity: 'error',
      comment:
        'Cross-package imports must use the package public entry point, not reach into its internals. See ADR-003.',
      from: { path: '^(apps|packages|services)/([^/]+)/' },
      to: {
        path: '^(apps|packages|services)/([^/]+)/src/',
        pathNot: [
          // importing your own package internals is fine
          '^$1/$2/',
        ],
      },
    },
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependency — indicates eroding module boundaries.',
      from: {},
      to: { circular: true },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment: 'Orphan module: not imported by anything and importing nothing.',
      from: { orphan: true, pathNot: ['\\.d\\.ts$', '(^|/)tests?/'] },
      to: {},
    },
    {
      name: 'services-not-imported-by-web',
      severity: 'error',
      comment:
        'The web app must not import backend services directly — it talks to them over generated API clients only.',
      from: { path: '^apps/web/' },
      to: { path: '^services/' },
    },
    {
      name: 'no-generated-edits',
      severity: 'error',
      comment: 'Generated clients are build artifacts; do not import from outside packages/contracts.',
      from: { pathNot: '^packages/contracts/' },
      to: { path: 'src/generated/' },
    },
  ],
  options: {
    doNotFollow: { path: 'node_modules' },
    exclude: { path: '(^|/)(node_modules|dist|build|\\.next|\\.gitnexus)/' },
    tsConfig: { fileName: 'tsconfig.base.json' },
    enhancedResolveOptions: { exportsFields: ['exports'], conditionNames: ['import', 'require', 'node'] },
  },
};
