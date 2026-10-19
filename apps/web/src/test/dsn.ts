/**
 * The one default for the database the browser suite uses — BUG-038.
 *
 * Read by `playwright.config.ts` for the API it starts, and by `global-setup.ts` for
 * the seeding tool it runs. `tools/e2e_region.py` deliberately has no default of its
 * own: two defaults for one database is the bug `tests/dbcheck.py` records.
 */

export const DATABASE_URL =
  process.env.JOURNEYLAB_DATABASE_URL ??
  'postgresql://journeylab:journeylab_dev_only@127.0.0.1:5700/journeylab';
