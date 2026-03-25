import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Auth protection is handled client-side in each dashboard page via
 * useAuthStore + useEffect redirect. This middleware is intentionally
 * transparent so the Zustand localStorage store (not cookies) is the
 * source of truth.
 */
export function proxy(request: NextRequest) {
  void request; // unused — pass everything through
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/onboarding"],
};
