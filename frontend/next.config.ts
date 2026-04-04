import type { NextConfig } from "next";
import path from "path";
import fs from "fs";

// Load root .env (one directory above frontend/) so we have a single source
// of truth for all environment variables.  Next.js normally only reads from
// the project root (frontend/), so we manually parse the parent .env and
// inject variables that are not already set in the process environment.
const rootEnvPath = path.resolve(__dirname, "../.env");
if (fs.existsSync(rootEnvPath)) {
  const lines = fs.readFileSync(rootEnvPath, "utf-8").split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIdx = trimmed.indexOf("=");
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const val = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, "");
    if (key && !(key in process.env)) {
      process.env[key] = val;
    }
  }
}

const nextConfig: NextConfig = {
  // Standalone output produces a minimal self-contained server bundle.
  // Required for the Dockerfile multi-stage build (reduces image ~600MB → ~150MB).
  output: "standalone",

  // Expose root .env NEXT_PUBLIC_* vars explicitly so they are available at
  // build time (required for static export and server components).
  env: {
    NEXT_PUBLIC_SUPABASE_URL:      process.env.NEXT_PUBLIC_SUPABASE_URL      ?? "",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
    NEXT_PUBLIC_API_URL:           process.env.NEXT_PUBLIC_API_URL           ?? "http://localhost:8000/api/v1",
    NEXT_PUBLIC_WS_URL:            process.env.NEXT_PUBLIC_WS_URL            ?? "ws://localhost:8000",
  },
};

export default nextConfig;
