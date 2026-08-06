import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // jsdom is required for the component and axe tests. Token tests are pure and
    // unaffected by it.
    environment: 'jsdom',
    globals: false,
  },
  esbuild: { jsx: 'automatic' },
});
