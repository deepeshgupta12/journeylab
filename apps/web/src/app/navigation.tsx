'use client';

/**
 * Application navigation — STEP-003.06.
 *
 * The item list lives here because it is product content; the filtering and the
 * accessibility behaviour live in `@journeylab/ui`. Each item names the operation
 * its destination performs, which is what allows the menu to be filtered from the
 * same matrix the server enforces (ADR-012).
 *
 * Routes come from FRONTEND_ARCHITECTURE §2. Only the ones whose steps exist are
 * listed; adding a link to an unbuilt route would be a 404 dressed as a feature.
 */

import { type NavItem, Navigation, type Role } from '@journeylab/ui';
import { usePathname } from 'next/navigation';

const ITEMS: NavItem[] = [
  { href: '/trips', label: 'Trips', operation: 'read_trip' },
  { href: '/trips/new', label: 'New trip', operation: 'create_trip' },
];

export function AppNavigation({ actorRole }: { actorRole: Role }) {
  const pathname = usePathname();
  return <Navigation items={ITEMS} actorRole={actorRole} currentPath={pathname ?? '/'} />;
}
