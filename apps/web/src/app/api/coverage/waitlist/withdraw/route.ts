import { forward } from '../../_proxy';

/** `POST /api/coverage/waitlist/withdraw` → `POST /waitlist:withdraw`. BUG-038, ADR-022. */

export const dynamic = 'force-dynamic';

export function POST(request: Request): Promise<Response> {
  return forward(request, '/waitlist:withdraw');
}
