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
  // NOTE: NEXT_PUBLIC_API_URL and NEXT_PUBLIC_WS_URL are read from .env.local
  // and must NOT be set here with fallbacks — the env block runs before
  // .env.local is parsed, so any ?? fallback here would silently override
  // the .env.local value.
  env: {
    NEXT_PUBLIC_SUPABASE_URL:      process.env.NEXT_PUBLIC_SUPABASE_URL      ?? "",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
  },

  // Performance optimizations
  compress: true,

  // Image optimization
  images: {
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Turbopack configuration (Next.js 16 default)
  // Leave empty to use Turbopack defaults with no webpack config
  turbopack: {},

  // Headers for better caching
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
        ],
      },
      {
        source: "/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      {
        source: "/app",
        destination: "/dashboard",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
