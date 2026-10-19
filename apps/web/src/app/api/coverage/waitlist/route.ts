import { forward } from '../_proxy';

/** `POST /api/coverage/waitlist` → `POST /waitlist` (`API-020`). BUG-038, ADR-022. */

export const dynamic = 'force-dynamic';

export function POST(request: Request): Promise<Response> {
  return forward(request, '/waitlist');
}
