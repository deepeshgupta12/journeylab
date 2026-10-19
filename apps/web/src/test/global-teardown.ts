import { runRegionTool } from './global-setup';

/** Removes what `global-setup.ts` seeded, and any waitlist rows the run created. BUG-038. */
export default function globalTeardown(): void {
  runRegionTool('remove');
}
