import { NextResponse } from "next/server";

/**
 * GET /api/health
 *
 * Lightweight liveness endpoint used by:
 *   - Docker HEALTHCHECK in frontend/Dockerfile
 *   - AWS ECS task definition healthCheck command
 *   - Load balancer target group health checks
 *
 * Returns 200 so ECS/ALB marks the container healthy and stops restart loops.
 */
export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "finshield-frontend",
      timestamp: new Date().toISOString(),
    },
    { status: 200 }
  );
}
